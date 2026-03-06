import base64
import hashlib
import hmac
import json
import threading
import uuid
from pathlib import Path


class LocalSecretStore:
    def __init__(self, *, key: str, file_path: Path) -> None:
        self._key = hashlib.sha256(key.encode("utf-8")).digest()
        self._path = file_path
        self._lock = threading.Lock()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, payload: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload), encoding="utf-8")

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            block = hmac.new(self._key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    def _encrypt(self, plaintext: str) -> str:
        raw = plaintext.encode("utf-8")
        nonce = uuid.uuid4().bytes
        stream = self._keystream(nonce, len(raw))
        cipher = bytes(a ^ b for a, b in zip(raw, stream))
        tag = hmac.new(self._key, nonce + cipher, hashlib.sha256).digest()
        payload = {
            "n": base64.b64encode(nonce).decode("ascii"),
            "c": base64.b64encode(cipher).decode("ascii"),
            "t": base64.b64encode(tag).decode("ascii"),
        }
        return json.dumps(payload)

    def _decrypt(self, token: str) -> str | None:
        try:
            payload = json.loads(token)
            nonce = base64.b64decode(payload["n"])
            cipher = base64.b64decode(payload["c"])
            tag = base64.b64decode(payload["t"])
            expected = hmac.new(self._key, nonce + cipher, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected):
                return None
            stream = self._keystream(nonce, len(cipher))
            plain = bytes(a ^ b for a, b in zip(cipher, stream))
            return plain.decode("utf-8")
        except Exception:
            return None

    def put(self, value: str, ref: str | None = None) -> str:
        with self._lock:
            payload = self._load()
            key = ref or f"sec_{uuid.uuid4().hex}"
            payload[key] = self._encrypt(value)
            self._save(payload)
            return key

    def get(self, ref: str) -> str | None:
        with self._lock:
            payload = self._load()
            token = payload.get(ref)
            if not isinstance(token, str):
                return None
            return self._decrypt(token)

    def delete(self, ref: str) -> bool:
        with self._lock:
            payload = self._load()
            if ref not in payload:
                return False
            del payload[ref]
            self._save(payload)
            return True

    @classmethod
    def rotate_file_key(cls, *, file_path: Path, old_key: str, new_key: str) -> int:
        old_store = cls(key=old_key, file_path=file_path)
        new_store = cls(key=new_key, file_path=file_path)

        with old_store._lock:
            encrypted_payload = old_store._load()
            if not encrypted_payload:
                new_store._save({})
                return 0

            plaintext_by_ref: dict[str, str] = {}
            for ref, token in encrypted_payload.items():
                if not isinstance(ref, str) or not isinstance(token, str):
                    raise ValueError("Secret store contains invalid payload entries")
                plaintext = old_store._decrypt(token)
                if plaintext is None:
                    raise ValueError("Secret store decryption failed. Ensure old key is correct.")
                plaintext_by_ref[ref] = plaintext

            rotated_payload: dict[str, str] = {}
            for ref, plaintext in plaintext_by_ref.items():
                rotated_payload[ref] = new_store._encrypt(plaintext)
            new_store._save(rotated_payload)
            return len(rotated_payload)
