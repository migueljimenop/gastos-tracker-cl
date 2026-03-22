from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.database import create_tables, get_db
from app.routers import categories, transactions, budgets, reports, scraper, importer, auth

_STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Registro de Gastos",
    description="API para registrar y analizar gastos de cuentas Santander y Falabella",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=_STATIC), name="static")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(reports.router)
app.include_router(importer.router)
app.include_router(scraper.router)


@app.get("/ui", include_in_schema=False)
def frontend():
    return FileResponse(_STATIC / "index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(_STATIC / "login.html")


@app.post("/admin/assign-orphan-transactions", tags=["admin"])
def assign_orphan_transactions(username: str, db: Session = Depends(get_db)):
    """Asigna todas las transacciones sin usuario al usuario indicado. Usar solo una vez para migrar datos existentes."""
    from app.models import Transaction, User
    user = db.query(User).filter(User.username == username).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")
    count = db.query(Transaction).filter(Transaction.user_id == None).update(  # noqa: E711
        {"user_id": user.id}, synchronize_session=False
    )
    db.commit()
    return {"assigned": count, "to_user": username}


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Registro de Gastos API"}
