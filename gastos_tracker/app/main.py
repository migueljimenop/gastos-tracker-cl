from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import create_tables
from app.routers import admin, categories, transactions, budgets, reports, scraper, importer, auth

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
app.include_router(admin.router)


@app.get("/ui", include_in_schema=False)
def frontend():
    return FileResponse(_STATIC / "index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(_STATIC / "login.html")


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Registro de Gastos API"}
