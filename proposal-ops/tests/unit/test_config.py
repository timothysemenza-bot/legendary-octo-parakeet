import importlib

import app.core.config as config


def test_config_uses_artifacts_dir_override(tmp_path, monkeypatch) -> None:
    with monkeypatch.context() as patch:
        patch.setenv("BOSSKEY_ARTIFACTS_DIR", tmp_path.as_posix())
        patch.delenv("BOSSKEY_DB_PATH", raising=False)
        patch.delenv("BOSSKEY_RFP_SOURCE_STORAGE_DIR", raising=False)
        patch.delenv("BOSSKEY_SECRET_STORE_PATH", raising=False)
        reloaded = importlib.reload(config)
        assert reloaded.DB_PATH == tmp_path / "bosskey_pursuit_os.sqlite3"
        assert reloaded.RFP_SOURCE_STORAGE_DIR == tmp_path / "rfp_source_documents"
        assert reloaded.SECRET_STORE_PATH == tmp_path / "secrets.json"

    importlib.reload(config)


def test_config_uses_explicit_db_path_override(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "isolated" / "bosskey-test.sqlite3"
    with monkeypatch.context() as patch:
        patch.delenv("BOSSKEY_ARTIFACTS_DIR", raising=False)
        patch.setenv("BOSSKEY_DB_PATH", db_path.as_posix())
        patch.delenv("BOSSKEY_RFP_SOURCE_STORAGE_DIR", raising=False)
        patch.delenv("BOSSKEY_SECRET_STORE_PATH", raising=False)
        reloaded = importlib.reload(config)
        assert reloaded.DB_PATH == db_path
        assert reloaded.DB_DIR == db_path.parent
        assert reloaded.DATABASE_URL == f"sqlite:///{db_path.as_posix()}"
        assert reloaded.RFP_SOURCE_STORAGE_DIR == db_path.parent / "rfp_source_documents"
        assert reloaded.SECRET_STORE_PATH == db_path.parent / "secrets.json"

    importlib.reload(config)
