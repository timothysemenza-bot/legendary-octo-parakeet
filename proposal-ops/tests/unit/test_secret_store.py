from pathlib import Path

from app.core.secret_store import LocalSecretStore


def test_local_secret_store_round_trip(tmp_path: Path) -> None:
    store = LocalSecretStore(key="unit-test-key", file_path=tmp_path / "secrets.json")
    ref = store.put("super-secret-token")
    assert ref.startswith("sec_")
    assert store.get(ref) == "super-secret-token"


def test_local_secret_store_update_and_delete(tmp_path: Path) -> None:
    store = LocalSecretStore(key="unit-test-key", file_path=tmp_path / "secrets.json")
    ref = store.put("token-a")
    store.put("token-b", ref=ref)
    assert store.get(ref) == "token-b"
    assert store.delete(ref) is True
    assert store.get(ref) is None


def test_local_secret_store_rotate_key_preserves_refs(tmp_path: Path) -> None:
    path = tmp_path / "secrets.json"
    old_store = LocalSecretStore(key="old-key", file_path=path)
    ref1 = old_store.put("token-1")
    ref2 = old_store.put("token-2")

    rotated = LocalSecretStore.rotate_file_key(file_path=path, old_key="old-key", new_key="new-key")
    assert rotated == 2

    new_store = LocalSecretStore(key="new-key", file_path=path)
    assert new_store.get(ref1) == "token-1"
    assert new_store.get(ref2) == "token-2"

    # Old key should no longer decrypt.
    old_again = LocalSecretStore(key="old-key", file_path=path)
    assert old_again.get(ref1) is None


def test_local_secret_store_rotate_key_raises_on_wrong_old_key(tmp_path: Path) -> None:
    path = tmp_path / "secrets.json"
    store = LocalSecretStore(key="correct-old", file_path=path)
    store.put("token-x")
    try:
        LocalSecretStore.rotate_file_key(file_path=path, old_key="wrong-old", new_key="new-key")
    except ValueError as exc:
        assert "old key is correct" in str(exc)
    else:
        raise AssertionError("Expected ValueError for wrong old key")
