"""Ed25519 key management and signatures for verification records."""

from __future__ import annotations

import hashlib
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .errors import KinemicaVerifyError


def _read_bytes(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise KinemicaVerifyError(f"{label} does not exist: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise KinemicaVerifyError(f"Could not read {label.lower()} from {path}: {exc}") from exc


def load_private_key(path: Path | str) -> Ed25519PrivateKey:
    path = Path(path)
    try:
        key = serialization.load_pem_private_key(_read_bytes(path, "Private key"), password=None)
    except (TypeError, ValueError) as exc:
        raise KinemicaVerifyError(f"Invalid unencrypted PEM private key: {path}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise KinemicaVerifyError(f"Private key is not Ed25519: {path}")
    return key


def load_public_key(path: Path | str) -> Ed25519PublicKey:
    path = Path(path)
    try:
        key = serialization.load_pem_public_key(_read_bytes(path, "Public key"))
    except (TypeError, ValueError) as exc:
        raise KinemicaVerifyError(f"Invalid PEM public key: {path}") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise KinemicaVerifyError(f"Public key is not Ed25519: {path}")
    return key


def public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def generate_keypair(private_path: Path | str, public_path: Path | str) -> str:
    """Generate an unencrypted Ed25519 PEM key pair without overwriting existing files."""

    private_path = Path(private_path)
    public_path = Path(public_path)

    if private_path.absolute() == public_path.absolute():
        raise KinemicaVerifyError("Private and public key paths must be different")

    for path in (private_path, public_path):
        if path.exists():
            raise KinemicaVerifyError(f"Refusing to overwrite existing key file: {path}")

    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    private_path.chmod(0o600)

    public_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    public_path.chmod(0o644)

    return public_key_id(public_key)
