"""Build encrypted payloads consumed by the Rust native runtime."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import marshal
import os
import sys
import zlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

from .native_format import NativeArtifactHeader


HKDF_CONTEXT = b"skjol-native-v1"


@dataclass(frozen=True)
class NativeMetadata:
    """Strict metadata schema decrypted and validated by Rust."""

    created: str
    license: str
    python_version: str
    source_hash: str
    expiration: Optional[str]
    machines: list[str]
    domains: list[str]
    anti_debug: bool


@dataclass(frozen=True)
class ProtectedArtifact:
    """In-memory native artifact and its generated Python launcher."""

    launcher: str
    payload: bytes
    runtime_id: str
    module_name: str
    format_version: int
    python_tag: str


class NativeArtifactBuilder:
    """Compile, compress, derive, and encrypt one native artifact."""

    def __init__(self, root_key: bytes, runtime_id: str):
        if len(root_key) != 32:
            raise ValueError("Native runtime root key must be exactly 32 bytes")
        self._root_key = root_key
        self.runtime_id = runtime_id
        self.module_name = f"skjol_runtime_{runtime_id}"

    def protect_source(
        self,
        source: str,
        filename: str,
        *,
        license_info: str,
        anti_debug: bool,
        artifact_id: Optional[bytes] = None,
        nonce: Optional[bytes] = None,
    ) -> ProtectedArtifact:
        artifact_id = artifact_id or os.urandom(16)
        nonce = nonce or os.urandom(12)
        metadata = self._metadata(source, license_info, anti_debug)
        metadata_bytes = json.dumps(
            asdict(metadata),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        code_bytes = marshal.dumps(compile(source, filename, "exec"))
        plaintext = metadata_bytes + zlib.compress(code_bytes, level=9)
        ciphertext_length = len(plaintext) + 16
        header = NativeArtifactHeader(
            python_major=sys.version_info.major,
            python_minor=sys.version_info.minor,
            metadata_length=len(metadata_bytes),
            ciphertext_length=ciphertext_length,
            nonce=nonce,
            artifact_id=artifact_id,
        )
        header_bytes = header.encode()
        ciphertext = self._encrypt(plaintext, header_bytes, artifact_id, nonce)
        payload = header_bytes + ciphertext
        return ProtectedArtifact(
            launcher=self._launcher(payload),
            payload=payload,
            runtime_id=self.runtime_id,
            module_name=self.module_name,
            format_version=NativeArtifactHeader.FORMAT_VERSION,
            python_tag=f"cp{sys.version_info.major}{sys.version_info.minor}",
        )

    def decrypt_for_test(self, payload: bytes) -> tuple[NativeMetadata, bytes]:
        """Validate Python/Rust test vectors without exposing a runtime API."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        header, ciphertext = NativeArtifactHeader.decode(payload)
        key = self._derive_key(header.artifact_id)
        plaintext = AESGCM(key).decrypt(header.nonce, ciphertext, payload[: header.HEADER_LENGTH])
        metadata_bytes = plaintext[: header.metadata_length]
        metadata = NativeMetadata(**json.loads(metadata_bytes.decode("utf-8")))
        return metadata, zlib.decompress(plaintext[header.metadata_length :])

    def _encrypt(self, plaintext: bytes, header: bytes, artifact_id: bytes, nonce: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:
            raise RuntimeError(
                "Rust runtime protection requires the 'cryptography' package"
            ) from exc
        return AESGCM(self._derive_key(artifact_id)).encrypt(nonce, plaintext, header)

    def _derive_key(self, artifact_id: bytes) -> bytes:
        """RFC 5869 HKDF-SHA256 with artifact ID as salt."""
        prk = hmac.new(artifact_id, self._root_key, hashlib.sha256).digest()
        return hmac.new(prk, HKDF_CONTEXT + b"\x01", hashlib.sha256).digest()

    @staticmethod
    def _metadata(source: str, license_info: str, anti_debug: bool) -> NativeMetadata:
        return NativeMetadata(
            created=datetime.now(timezone.utc).isoformat(),
            license=license_info,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
            source_hash=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            expiration=None,
            machines=[],
            domains=[],
            anti_debug=anti_debug,
        )

    def _launcher(self, payload: bytes) -> str:
        encoded = base64.b64encode(payload).decode("ascii")
        return (
            f"from {self.module_name} import run as __skjol_native_run\n"
            f"__skjol_native_run(__name__, __file__, b'{encoded}')\n"
        )
