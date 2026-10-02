import sys
import os
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import psycopg2
from app.core.config import settings

conn = psycopg2.connect(settings.DATABASE_URL.replace('+psycopg2', ''))
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
tables = [r[0] for r in cur.fetchall()]

print(f"Total tables in public schema: {len(tables)}")
for t in tables:
    cur.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='{t}';")
    cols = cur.fetchone()[0]
    print(f"  - {t:<35} ({cols} columns)")

cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name='skills' AND column_name='embedding';")
col_info = cur.fetchone()
print(f"\nskills.embedding column: name={col_info[0]}, type={col_info[1]}, udt={col_info[2]}")

cur.execute("SELECT version_num FROM alembic_version;")
version = cur.fetchall()
print(f"\nalembic_version: {version}")

cur.execute("SELECT extname, extversion FROM pg_extension;")
extensions = cur.fetchall()
print(f"\npg_extensions: {extensions}")

cur.close()
conn.close()
