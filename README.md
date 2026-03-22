# gastos-tracker-cl

Aplicacion web para gestionar gastos personales de cuentas Santander y Falabella en Chile.

## Stack

- FastAPI
- SQLAlchemy 2.0
- SQLite
- Pydantic v2
- Tailwind CSS + JavaScript vanilla
- Playwright para scrapers bancarios

## Estructura

```text
gastos_tracker/
	app/
		routers/      # Endpoints FastAPI
		services/     # Logica de negocio
		importers/    # Importadores de cartolas CSV/XLS/XLSX
		scrapers/     # Scrapers bancarios con Playwright
		static/       # Frontend servido como archivos estaticos
	tests/          # Suite de pruebas con pytest
```

## Instalacion

```bash
cd gastos_tracker
pip install -r requirements.txt
```

## Ejecucion local

```bash
cd gastos_tracker
uvicorn app.main:app --reload
```

Rutas utiles:

- API base: `http://127.0.0.1:8000/`
- UI principal: `http://127.0.0.1:8000/ui`
- Login: `http://127.0.0.1:8000/login`

## Superusuario

El proyecto ahora soporta el atributo `is_superuser` en el modelo de usuario.

Para crear o promover un superusuario:

```bash
cd gastos_tracker
python -m app.create_superuser --username admin --password "tu_clave_segura"
```

El comando:

- crea la tabla de usuarios si no existe
- agrega la columna `is_superuser` si la base ya existia
- crea el usuario si no existe
- o actualiza un usuario existente para dejarlo activo y con privilegios de superusuario

## Dependencias

Se ajustaron algunas versiones para compatibilidad con el entorno actual de Python del workspace:

- `sqlalchemy>=2.0.48`
- `pandas>=3.0.1`
- `playwright>=1.58.0`
- `bcrypt<5`

## Testing

```bash
cd gastos_tracker
pytest -v
```

Las pruebas usan overrides de dependencias en `tests/conftest.py` para evitar autenticacion real.

## Documentacion de cambios

El historial de cambios del proyecto se mantiene en `CHANGELOG.md`.
