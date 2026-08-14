"""Binary envelope for the Rust native runtime."""

from __future__ import annotations

import struct
from dataclasses import dataclass


class NativeFormatError(ValueError):
    """Raised when a native artifact envelope is malformed."""


@dataclass(frozen=True)
class NativeArtifactHeader:
    """Validated fixed-width header authenticated as AES-GCM AAD."""

    MAGIC = b"SKJNR001"
    FORMAT_VERSION = 1
    CIPHER_SUITE = 1
    STRUCT = struct.Struct("<8sHHHHBBHIQ12s16s")
    HEADER_LENGTH = STRUCT.size
    MAX_METADATA_LENGTH = 1024 * 1024
    MAX_CIPHERTEXT_LENGTH = 64 * 1024 * 1024

    python_major: int
    python_minor: int
    metadata_length: int
    ciphertext_length: int
    nonce: bytes
    artifact_id: bytes
    flags: int = 0

    def encode(self) -> bytes:
        self._validate()
        return self.STRUCT.pack(
            self.MAGIC,
            self.FORMAT_VERSION,
            self.HEADER_LENGTH,
            self.CIPHER_SUITE,
            self.flags,
            self.python_major,
            self.python_minor,
            0,
            self.metadata_length,
            self.ciphertext_length,
            self.nonce,
            self.artifact_id,
        )

    @classmethod
    def decode(cls, artifact: bytes) -> tuple["NativeArtifactHeader", bytes]:
        if len(artifact) < cls.HEADER_LENGTH:
            raise NativeFormatError("Native artifact is shorter than its fixed header")
        fields = cls.STRUCT.unpack_from(artifact)
        cls._validate_fixed_fields(fields)
        header = cls(
            python_major=fields[5],
            python_minor=fields[6],
            metadata_length=fields[8],
            ciphertext_length=fields[9],
            nonce=fields[10],
            artifact_id=fields[11],
            flags=fields[4],
        )
        header._validate()
        expected_length = cls.HEADER_LENGTH + header.ciphertext_length
        if len(artifact) != expected_length:
            raise NativeFormatError(
                f"Native artifact length mismatch: expected {expected_length}, got {len(artifact)}"
            )
        return header, artifact[cls.HEADER_LENGTH:]

    @classmethod
    def _validate_fixed_fields(cls, fields: tuple[object, ...]) -> None:
        magic, version, header_length, cipher_suite = fields[:4]
        reserved = fields[7]
        if magic != cls.MAGIC:
            raise NativeFormatError("Invalid native artifact magic")
        if version != cls.FORMAT_VERSION:
            raise NativeFormatError(f"Unsupported native artifact version: {version}")
        if header_length != cls.HEADER_LENGTH:
            raise NativeFormatError(f"Unsupported native header length: {header_length}")
        if cipher_suite != cls.CIPHER_SUITE:
            raise NativeFormatError(f"Unsupported native cipher suite: {cipher_suite}")
        if reserved != 0:
            raise NativeFormatError("Native artifact reserved field must be zero")

    def _validate(self) -> None:
        if self.flags != 0:
            raise NativeFormatError(f"Unsupported native artifact flags: {self.flags:#x}")
        if not 0 < self.python_major <= 255 or not 0 <= self.python_minor <= 255:
            raise NativeFormatError("Invalid Python version in native artifact")
        if not 0 <= self.metadata_length <= self.MAX_METADATA_LENGTH:
            raise NativeFormatError("Native metadata length exceeds the supported limit")
        if not 16 <= self.ciphertext_length <= self.MAX_CIPHERTEXT_LENGTH:
            raise NativeFormatError("Native ciphertext length exceeds the supported limit")
        if len(self.nonce) != 12:
            raise NativeFormatError("AES-GCM nonce must be 12 bytes")
        if len(self.artifact_id) != 16:
            raise NativeFormatError("Native artifact ID must be 16 bytes")
