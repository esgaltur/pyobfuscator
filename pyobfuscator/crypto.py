# -*- coding: utf-8 -*-
"""
Shared Cryptographic Engine for PyObfuscator.

Provides AES-256-GCM encryption with PBKDF2 key derivation.
Falls back to a stream cipher with HMAC if cryptography library is not available.
"""

import hashlib
import hmac
import os
import platform
import struct
import subprocess
import sys
import uuid
from typing import List

from .constants import CryptoConstants

# Try to use cryptography library for AES
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class CryptoEngine:
    """
    AES-256-GCM encryption with PBKDF2 key derivation.
    Falls back to stream cipher with HMAC if cryptography not available.
    """

    # Use constants from the constants module
    SALT_SIZE = CryptoConstants.SALT_SIZE
    NONCE_SIZE = CryptoConstants.NONCE_SIZE
    KEY_SIZE = CryptoConstants.KEY_SIZE
    ITERATIONS = CryptoConstants.PBKDF2_ITERATIONS

    def __init__(self, key: bytes):
        self.master_key = key

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key using PBKDF2-HMAC-SHA256."""
        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.KEY_SIZE,
                salt=salt,
                iterations=self.ITERATIONS,
            )
            return kdf.derive(self.master_key)
        else:
            return self._pbkdf2_sha256(self.master_key, salt, self.ITERATIONS, self.KEY_SIZE)

    def _pbkdf2_sha256(self, password: bytes, salt: bytes, iterations: int, dklen: int) -> bytes:
        """Pure Python PBKDF2-HMAC-SHA256."""
        dk = b''
        block_num = 1
        while len(dk) < dklen:
            u = hmac.new(password, salt + struct.pack('>I', block_num), hashlib.sha256).digest()
            result = u
            for _ in range(iterations - 1):
                u = hmac.new(password, u, hashlib.sha256).digest()
                result = bytes(x ^ y for x, y in zip(result, u))
            dk += result
            block_num += 1
        return dk[:dklen]

    def _generate_keystream(self, key: bytes, nonce: bytes, length: int) -> bytes:
        """Generate keystream using counter mode."""
        keystream = bytearray()
        counter = 0
        while len(keystream) < length:
            block = hashlib.sha256(key + nonce + struct.pack('<Q', counter)).digest()
            keystream.extend(block)
            counter += 1
        return bytes(keystream[:length])

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        key = self._derive_key(salt)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data, None)
        else:
            # Fallback encryption
            keystream = self._generate_keystream(key, nonce, len(data))
            ct = bytes(d ^ k for d, k in zip(data, keystream))
            auth_key = hashlib.sha256(key + b'auth').digest()
            tag = hmac.new(auth_key, nonce + ct, hashlib.sha256).digest()[:16]
            ciphertext = ct + tag

        return salt + nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt AES-256-GCM encrypted data."""
        salt = data[:self.SALT_SIZE]
        nonce = data[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = data[self.SALT_SIZE + self.NONCE_SIZE:]
        key = self._derive_key(salt)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        else:
            ct = ciphertext[:-16]
            tag = ciphertext[-16:]
            auth_key = hashlib.sha256(key + b'auth').digest()
            expected_tag = hmac.new(auth_key, nonce + ct, hashlib.sha256).digest()[:16]
            if not hmac.compare_digest(tag, expected_tag):
                raise ValueError("Authentication failed")
            keystream = self._generate_keystream(key, nonce, len(ct))
            return bytes(c ^ k for c, k in zip(ct, keystream))


def get_machine_id() -> str:
    """
    Get a unique machine identifier for hardware binding.

    Returns:
        A hash of machine-specific information.
    """
    machine_info: List[str] = []

    # Platform info
    machine_info.append(platform.node())
    machine_info.append(platform.machine())
    machine_info.append(platform.processor())

    # Try to get MAC address
    try:
        mac = uuid.getnode()
        if mac != uuid.getnode():  # Check if it's a random MAC
            mac = 0
        machine_info.append(str(mac))
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception:
        pass

    # Try to get disk serial (Windows)
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'serialnumber'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.split('\n')
                        if l.strip() and l.strip() != 'SerialNumber']
                if lines:
                    machine_info.append(lines[0])
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception:
            pass

    # Create hash
    combined = '|'.join(machine_info)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]
