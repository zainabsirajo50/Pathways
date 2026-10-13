"""FastAPI factory; does not create tables, migrate, seed, or approve records."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from app.config import Settings, get_settings
from app.api.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        app.state.session_factory = sessionmaker(engine, autoflush=False, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title='Pathways Catalog API', version='0.1.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                       allow_credentials=False, allow_methods=['GET'],
                       allow_headers=['Accept', 'Content-Type'])

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        # Avoid returning SQL, connection details, or credential-bearing exceptions.
        return JSONResponse(status_code=503, content={'detail': 'Catalog temporarily unavailable'})

    app.include_router(router)
    return app
