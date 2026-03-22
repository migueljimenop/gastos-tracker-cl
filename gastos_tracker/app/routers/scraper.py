from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import BankSource, Transaction
from app.schemas import ScrapeRequest, ScrapeResult
from app.scrapers import SantanderScraper, FalabellaScraper
from app.services.categorizer import auto_categorize

router = APIRouter(prefix="/scraper", tags=["scraper"], dependencies=[Depends(get_current_user)])


@router.post("/run", response_model=ScrapeResult)
async def run_scraper(request: ScrapeRequest, db: Session = Depends(get_db)):
    errors: list[str] = []
    raw_transactions = []

    try:
        if request.bank == BankSource.SANTANDER:
            if not settings.SANTANDER_RUT or not settings.SANTANDER_PASSWORD:
                raise HTTPException(status_code=400, detail="Santander credentials not configured in .env")
            scraper = SantanderScraper(settings.SANTANDER_RUT, settings.SANTANDER_PASSWORD)

        elif request.bank == BankSource.FALABELLA:
            if not settings.FALABELLA_RUT or not settings.FALABELLA_PASSWORD:
                raise HTTPException(status_code=400, detail="Falabella credentials not configured in .env")
            scraper = FalabellaScraper(settings.FALABELLA_RUT, settings.FALABELLA_PASSWORD)

        else:
            raise HTTPException(status_code=400, detail="Bank source not supported for scraping")

        raw_transactions = await scraper.fetch_transactions(months_back=request.months_back)

    except HTTPException:
        raise
    except Exception as exc:
        errors.append(str(exc))

    # Persist new transactions (skip duplicates by external_id)
    new_count = 0
    for raw in raw_transactions:
        if raw.external_id:
            exists = db.query(Transaction).filter(Transaction.external_id == raw.external_id).first()
            if exists:
                continue

        category_id = auto_categorize(raw.description, db)
        tx = Transaction(
            date=raw.date,
            description=raw.description,
            amount=raw.amount,
            transaction_type=raw.transaction_type,
            bank_source=raw.bank_source,
            external_id=raw.external_id,
            category_id=category_id,
        )
        db.add(tx)
        new_count += 1

    db.commit()

    return ScrapeResult(
        bank=request.bank,
        transactions_found=len(raw_transactions),
        transactions_new=new_count,
        errors=errors,
    )
