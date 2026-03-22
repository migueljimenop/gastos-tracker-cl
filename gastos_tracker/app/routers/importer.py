"""
File upload endpoints for importing bank cartolas (account statements).

Usage:
  POST /import/santander   — upload a Santander cartola (CSV or Excel)
  POST /import/falabella   — upload a Falabella CMR cartola (CSV or Excel)

Both endpoints accept multipart/form-data with a single file field named "file".
Duplicate transactions are detected by external_id and skipped automatically.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.importers import SantanderImporter, FalabellaImporter
from app.importers.base import BaseImporter
from app.models import Transaction, User
from app.schemas import ImportResult
from app.services.categorizer import auto_categorize

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(get_current_user)])

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _import_file(
    file: UploadFile,
    importer: BaseImporter,
    bank_label: str,
    db: Session,
    user_id: int,
) -> ImportResult:
    if file.size and file.size > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 10 MB")

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 10 MB")

    errors: list[str] = []
    try:
        raw_transactions = importer.parse(content, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {exc}")

    new_count = 0
    skipped_count = 0

    for raw in raw_transactions:
        # Deduplicate by external_id
        if raw.external_id:
            exists = db.query(Transaction).filter(
                Transaction.external_id == raw.external_id,
                Transaction.user_id == user_id,
            ).first()
            if exists:
                skipped_count += 1
                continue

        try:
            category_id = auto_categorize(raw.description, db)
            tx = Transaction(
                date=raw.date,
                description=raw.description,
                amount=raw.amount,
                transaction_type=raw.transaction_type,
                bank_source=raw.bank_source,
                external_id=raw.external_id,
                category_id=category_id,
                user_id=user_id,
            )
            db.add(tx)
            new_count += 1
        except Exception as exc:
            errors.append(f"Error al guardar '{raw.description}': {exc}")

    db.commit()

    return ImportResult(
        bank=bank_label,
        filename=file.filename or "upload",
        transactions_found=len(raw_transactions),
        transactions_new=new_count,
        transactions_skipped=skipped_count,
        errors=errors,
    )


@router.post("/santander", response_model=ImportResult, summary="Importar cartola Santander Chile")
async def import_santander(
    file: UploadFile = File(..., description="Archivo de cartola exportado desde banco.santander.cl (.xlsx o .csv)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _import_file(file, SantanderImporter(), "santander", db, current_user.id)


@router.post("/falabella", response_model=ImportResult, summary="Importar cartola Falabella CMR")
async def import_falabella(
    file: UploadFile = File(..., description="Archivo de cartola exportado desde falabella.com CMR (.xlsx o .csv)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _import_file(file, FalabellaImporter(), "falabella", db, current_user.id)
