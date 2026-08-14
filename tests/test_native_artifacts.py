"""Tests for the authenticated Rust-runtime artifact envelope."""

import marshal
import sys

import pytest

from pyobfuscator.artifacts import (
    NativeArtifactBuilder,
    NativeArtifactHeader,
    NativeFormatError,
)


ROOT_KEY = bytes(range(32))
ARTIFACT_ID = bytes(range(16))
NONCE = bytes(range(12))


def build_artifact(source: str = 'print("native vector")\n'):
    pytest.importorskip("cryptography")
    builder = NativeArtifactBuilder(ROOT_KEY, "testvector")
    artifact = builder.protect_source(
        source,
        "vector.py",
        license_info="test license",
        anti_debug=False,
        artifact_id=ARTIFACT_ID,
        nonce=NONCE,
    )
    return builder, artifact


def test_native_artifact_round_trip_has_versioned_authenticated_header() -> None:
    builder, artifact = build_artifact()

    header, ciphertext = NativeArtifactHeader.decode(artifact.payload)
    metadata, marshaled = builder.decrypt_for_test(artifact.payload)
    code = marshal.loads(marshaled)

    assert header.python_major == sys.version_info.major
    assert header.python_minor == sys.version_info.minor
    assert header.nonce == NONCE
    assert header.artifact_id == ARTIFACT_ID
    assert len(ciphertext) == header.ciphertext_length
    assert metadata.license == "test license"
    assert metadata.anti_debug is False
    assert code.co_filename == "vector.py"
    assert artifact.module_name == "skjol_runtime_testvector"
    assert "native vector" not in artifact.launcher
    assert ROOT_KEY.hex() not in artifact.launcher


def test_native_artifact_rejects_malformed_header_before_decryption() -> None:
    _, artifact = build_artifact()
    damaged = bytearray(artifact.payload)
    damaged[0] ^= 1

    with pytest.raises(NativeFormatError, match="magic"):
        NativeArtifactHeader.decode(bytes(damaged))


def test_native_artifact_authentication_rejects_ciphertext_tampering() -> None:
    cryptography = pytest.importorskip("cryptography.exceptions")
    builder, artifact = build_artifact()
    damaged = bytearray(artifact.payload)
    damaged[-1] ^= 1

    with pytest.raises(cryptography.InvalidTag):
        builder.decrypt_for_test(bytes(damaged))


def test_native_artifact_authentication_rejects_wrong_root_key() -> None:
    cryptography = pytest.importorskip("cryptography.exceptions")
    _, artifact = build_artifact()
    wrong_builder = NativeArtifactBuilder(b"x" * 32, "testvector")

    with pytest.raises(cryptography.InvalidTag):
        wrong_builder.decrypt_for_test(artifact.payload)


@pytest.mark.parametrize("root_key", [b"", b"short", b"x" * 31, b"x" * 33])
def test_native_builder_requires_a_256_bit_root_key(root_key: bytes) -> None:
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        NativeArtifactBuilder(root_key, "invalid")
