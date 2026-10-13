import os
from pathlib import Path
import secrets
import subprocess
import sys
import psycopg
from psycopg import sql
from dotenv import dotenv_values
backend = Path(__file__).resolve().parents[1]
password = dotenv_values(backend / '.env.admin')['PATHWAYS_POSTGRES_ADMIN_PASSWORD']
name = 'pathways_test_' + secrets.token_hex(8)
with psycopg.connect(host='localhost',dbname='postgres',user='postgres',password=password,autocommit=True) as admin:
    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        env = os.environ.copy()
        env['TEST_DATABASE_URL'] = f'postgresql+psycopg://postgres:{password}@localhost:5432/{name}'
        result = subprocess.run([sys.executable,'-m','pytest','-q'],cwd=backend,env=env)
    finally:
        assert name.startswith('pathways_test_')
        admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
sys.exit(result.returncode)
