from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import create_tables
from app.routers import categories, transactions, budgets, reports, scraper, importer


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

app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(reports.router)
app.include_router(importer.router)
app.include_router(scraper.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Registro de Gastos API"}
