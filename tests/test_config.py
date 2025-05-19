from app.core.config import Settings


def test_create_schema_is_read_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("CREATE_SCHEMA", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite+aiosqlite:///:memory:\nCREATE_SCHEMA=true\n")
    assert Settings(_env_file=env_file).CREATE_SCHEMA is True


def test_create_schema_defaults_to_false(monkeypatch):
    monkeypatch.delenv("CREATE_SCHEMA", raising=False)
    assert Settings(_env_file=None).CREATE_SCHEMA is False
