# Changelog

Todos los cambios relevantes del proyecto se registran en este archivo.

## [Unreleased]

### Added

- Soporte para `is_superuser` en el modelo y schema de usuario.
- Script CLI `python -m app.create_superuser` para crear o promover administradores.
- Archivo `.github/copilot-instructions.md` con convenciones del workspace para agentes.

### Changed

- Documentacion principal del proyecto ampliada en `README.md`.
- Dependencias actualizadas para compatibilidad con Python 3.14 en este entorno.

### Fixed

- Correccion de incompatibilidad entre SQLAlchemy y Python 3.14.
- Correccion de compatibilidad de `bcrypt` para hashing de passwords con `passlib`.