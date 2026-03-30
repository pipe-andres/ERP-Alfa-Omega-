1. Levanta el contenedor PostgreSQL (no lo hagas aún; instrucciones para cuando lo necesites):
   - `docker compose -f docker-compose.postgres.yml up -d`
2. Exporta variables de entorno (ejemplo Windows PowerShell):
   - `$env:DATABASE_URL='postgresql+asyncpg://inventario_user:inventario_pass@localhost:5432/inventario'`
   - `$env:POSTGRES_TEST_URL='postgresql+asyncpg://inventario_user:inventario_pass@localhost:5432/inventario_test'`
3. Crear migraciones y ejecutar:
   - `alembic -c migrations/alembic.ini revision --autogenerate -m "initial_postgres_schema"`
   - `alembic -c migrations/alembic.ini upgrade head`
4. Ejecutar tests apuntando a `POSTGRES_TEST_URL`.
