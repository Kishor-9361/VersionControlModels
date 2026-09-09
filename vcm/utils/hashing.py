"""Cryptographic hashing utilities for models and data files."""

from __future__ import annotations

import hashlib
import os


def compute_file_hash(filepath: str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file, returning 'sha256:<hex_digest>' format."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot compute hash for non-existent file: {filepath}")

    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return f"sha256:{hasher.hexdigest()}"


def compute_data_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"
