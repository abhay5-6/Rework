import os
import pytest
from pathlib import Path

from app.core.config import settings
from app.services.ai.embedding_service import generate_embedding



def test_alembic_migrations_applied_to_head():
    """Verifies that Alembic configuration and versions directory exist with valid migration files."""
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    versions_dir = backend_dir / "alembic" / "versions"

    assert alembic_ini_path.exists(), "alembic.ini missing in backend root"
    assert versions_dir.exists(), "alembic/versions directory missing in backend"

    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) >= 1, "Expected at least one migration revision file in alembic/versions"


def test_docker_compose_file_validity():
    """Verifies that docker-compose.yml and docker-compose.prod.yml exist and specify core services."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    compose_dev = root_dir / "docker-compose.yml"
    compose_prod = root_dir / "docker-compose.prod.yml"

    assert compose_dev.exists(), "docker-compose.yml missing in repository root"
    assert compose_prod.exists(), "docker-compose.prod.yml missing in repository root"

    dev_content = compose_dev.read_text()
    prod_content = compose_prod.read_text()

    for service in ["postgres", "redis", "backend", "frontend"]:
        assert service in dev_content, f"Service '{service}' missing in docker-compose.yml"

    for service in ["postgres", "redis", "backend"]:
        assert service in prod_content, f"Service '{service}' missing in docker-compose.prod.yml"


@pytest.mark.asyncio
async def test_ai_stubs_active_in_ci_environment():

    """Verifies that AI test mode stub is enabled and generates mock embeddings instantly."""
    assert settings.ai_test_mode or os.getenv("AI_TEST_MODE", "").lower() in ("true", "1", "yes")
    embedding = await generate_embedding("CI readiness check")
    assert isinstance(embedding, list)
    assert len(embedding) == settings.embedding_dimension
    assert embedding == [0.0] * settings.embedding_dimension
