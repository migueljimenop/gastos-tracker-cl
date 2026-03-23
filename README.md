# Gastos Tracker CL

Aplicación web para registrar, importar y analizar gastos de cuentas **Santander** y **Falabella** (Chile). Permite cargar archivos Excel del banco, clasificar por categorías, gestionar presupuestos y exportar reportes.

---

## Estado actual del proyecto

| Módulo | Estado |
|---|---|
| API REST (FastAPI) | Funcionando |
| Autenticación con JWT | Funcionando |
| Multi-usuario (datos aislados por cuenta) | Funcionando |
| Importador Santander (Excel) | Funcionando |
| Importador Falabella (Excel) | Funcionando |
| Categorización de transacciones | Funcionando |
| Presupuestos por categoría | Funcionando |
| Reportes (resumen, por categoría, tendencias) | Funcionando |
| Exportación CSV / Excel | Funcionando |
| Interfaz web (HTML/JS) | Funcionando |
| Scraper automatizado (Playwright) | En desarrollo |

Usuarios creados: **2 usuarios activos**. El sistema no permite registro libre — para acceder debes contactar al administrador.

---

## Acceso

> El registro de nuevos usuarios **no está habilitado de forma libre**. Para solicitar acceso, escribe a:
> **migueljimeno.p@gmail.com**

---

## Requisitos

- Python 3.11+
- pip

---

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/migueljimenop/gastos-tracker-cl.git
cd gastos-tracker-cl/gastos_tracker

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno (opcional)
# Crea un archivo .env en gastos_tracker/ con:
# SECRET_KEY=tu_clave_secreta
# JWT_EXPIRE_HOURS=24

# 4. Iniciar la aplicación
uvicorn app.main:app --reload
```

La app queda disponible en: [http://localhost:8000](http://localhost:8000)

---

## URLs principales

| URL | Descripción |
|---|---|
| `http://localhost:8000/` | Health check de la API |
| `http://localhost:8000/login` | Pantalla de inicio de sesión |
| `http://localhost:8000/ui` | Interfaz web principal |
| `http://localhost:8000/docs` | Documentación interactiva (Swagger) |
| `http://localhost:8000/redoc` | Documentación alternativa (ReDoc) |

---

## Funcionalidades principales

### Importar movimientos
Sube archivos Excel descargados directamente desde el banco:
- **Santander**: Cartola en formato `.xlsx`
- **Falabella**: Estado de cuenta en formato `.xlsx`

Endpoint: `POST /import/upload`

### Transacciones
- Listar con filtros (fecha, banco, categoría, tipo)
- Crear manualmente
- Editar y eliminar (incluyendo eliminación masiva)

### Categorías
- Crear categorías personalizadas
- Asignar colores y descripciones
- Las transacciones sin categoría quedan como "Sin categoría"

### Presupuestos
- Definir límites de gasto mensual por categoría
- Consultar avance vs presupuesto

### Reportes
- Resumen general por período
- Desglose por categoría
- Tendencias mensuales
- Exportación a CSV o Excel

---

## Estructura del proyecto

```
gastos_tracker/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── models.py            # Modelos SQLAlchemy (User, Transaction, Category, Budget)
│   ├── schemas.py           # Schemas Pydantic
│   ├── database.py          # Configuración SQLite
│   ├── config.py            # Variables de entorno
│   ├── dependencies.py      # Dependencias de autenticación
│   ├── routers/             # Endpoints REST
│   │   ├── auth.py
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   ├── budgets.py
│   │   ├── reports.py
│   │   ├── importer.py
│   │   └── scraper.py
│   ├── services/            # Lógica de negocio
│   │   ├── auth.py          # JWT + bcrypt
│   │   ├── categorizer.py
│   │   └── exporter.py
│   ├── importers/           # Parsers de archivos bancarios
│   │   ├── santander.py
│   │   └── falabella.py
│   ├── scrapers/            # Automatización web (Playwright)
│   │   ├── santander.py
│   │   └── falabella.py
│   └── static/              # Frontend web
│       ├── index.html
│       └── login.html
├── tests/
│   ├── conftest.py
│   └── test_importers.py
└── requirements.txt
```

---

## Ejecutar tests

```bash
cd gastos_tracker
pytest
```

---

## Notas

- La base de datos es **SQLite** (`gastos.db`), local y sin servidor externo.
- Cada usuario solo ve sus propias transacciones — los datos están aislados por cuenta.
- El archivo `.env` no se sube al repositorio (está en `.gitignore`).
