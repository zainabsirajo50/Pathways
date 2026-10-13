"""Environment configuration; credentials are never included in responses."""
from dataclasses import dataclass, field
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINS = ('http://localhost:5173', 'http://127.0.0.1:5173')


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    cors_origins: tuple[str, ...] = DEFAULT_ORIGINS

    def __post_init__(self):
        try:
            url = make_url(self.database_url)
            if url.drivername != 'postgresql+psycopg' or not url.database:
                raise ValueError
        except Exception:
            raise ValueError('DATABASE_URL must use postgresql+psycopg and specify a database') from None
        for origin in self.cors_origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
                raise ValueError('CORS_ORIGINS must contain HTTP(S) origins without paths or credentials')


def get_settings() -> Settings:
    values = {**dotenv_values(BACKEND / '.env'), **os.environ}
    url = values.get('DATABASE_URL')
    if not url:
        raise ValueError('DATABASE_URL is required; configure backend/.env')
    origins = tuple(part.strip() for part in values.get('CORS_ORIGINS', ','.join(DEFAULT_ORIGINS)).split(',') if part.strip())
    return Settings(database_url=url, cors_origins=origins)
