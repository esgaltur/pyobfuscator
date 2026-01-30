"""
Runtime Protection with PYD (Cython-compiled) runtime module.

This creates protected Python files that require a compiled .pyd runtime
module to execute, making reverse engineering much harder.

Uses AES-256-GCM encryption with PBKDF2 key derivation for strong protection.

Features:
- AES-256-GCM encryption with PBKDF2 key derivation
- Cython compilation to native binary (.pyd/.so)
- Anti-debugging detection
- Time-based license expiration
- Hardware/machine binding
- Code integrity verification
- Memory protection (sensitive data clearing)
"""

import ast
import base64
import hashlib
import hmac
import marshal
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import uuid
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Try to use cryptography library for AES, fallback to pure Python implementation
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

    If cryptography library is not available, falls back to a stronger
    XOR-based stream cipher with multiple rounds.
    """

    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    ITERATIONS = 100000  # PBKDF2 iterations

    def __init__(self, key: bytes):
        self.master_key = key
        self._salt = os.urandom(self.SALT_SIZE)

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
            # Pure Python PBKDF2 implementation
            return self._pbkdf2_sha256(self.master_key, salt, self.ITERATIONS, self.KEY_SIZE)

    def _pbkdf2_sha256(self, password: bytes, salt: bytes, iterations: int, dklen: int) -> bytes:
        """Pure Python PBKDF2-HMAC-SHA256 implementation."""
        def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
            return hmac.new(key, msg, hashlib.sha256).digest()

        def _xor_bytes(a: bytes, b: bytes) -> bytes:
            return bytes(x ^ y for x, y in zip(a, b))

        dk = b''
        block_num = 1
        while len(dk) < dklen:
            u = _hmac_sha256(password, salt + struct.pack('>I', block_num))
            result = u
            for _ in range(iterations - 1):
                u = _hmac_sha256(password, u)
                result = _xor_bytes(result, u)
            dk += result
            block_num += 1
        return dk[:dklen]

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Returns: salt (16) + nonce (12) + ciphertext + tag (16)
        """
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        key = self._derive_key(salt)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data, None)  # includes auth tag
        else:
            # Fallback: ChaCha20-like stream cipher with HMAC authentication
            ciphertext = self._fallback_encrypt(key, nonce, data)

        return salt + nonce + ciphertext

    def _fallback_encrypt(self, key: bytes, nonce: bytes, data: bytes) -> bytes:
        """
        Fallback encryption using a stream cipher construction.
        Uses CTR mode with HMAC-SHA256 for authentication.
        """
        # Generate keystream using counter mode
        keystream = self._generate_keystream(key, nonce, len(data))

        # XOR data with keystream
        ciphertext = bytes(d ^ k for d, k in zip(data, keystream))

        # Add HMAC for authentication
        auth_key = hashlib.sha256(key + b'auth').digest()
        tag = hmac.new(auth_key, nonce + ciphertext, hashlib.sha256).digest()[:16]

        return ciphertext + tag

    def _generate_keystream(self, key: bytes, nonce: bytes, length: int) -> bytes:
        """Generate keystream using counter mode."""
        keystream = bytearray()
        counter = 0
        while len(keystream) < length:
            block_input = key + nonce + struct.pack('<Q', counter)
            block = hashlib.sha256(block_input).digest()
            keystream.extend(block)
            counter += 1
        return bytes(keystream[:length])

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM.

        Input: salt (16) + nonce (12) + ciphertext + tag (16)
        """
        salt = data[:self.SALT_SIZE]
        nonce = data[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = data[self.SALT_SIZE + self.NONCE_SIZE:]

        key = self._derive_key(salt)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        else:
            return self._fallback_decrypt(key, nonce, ciphertext)

    def _fallback_decrypt(self, key: bytes, nonce: bytes, ciphertext_with_tag: bytes) -> bytes:
        """Fallback decryption with HMAC verification."""
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]

        # Verify HMAC
        auth_key = hashlib.sha256(key + b'auth').digest()
        expected_tag = hmac.new(auth_key, nonce + ciphertext, hashlib.sha256).digest()[:16]

        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Authentication failed - data may be corrupted or tampered")

        # Decrypt
        keystream = self._generate_keystream(key, nonce, len(ciphertext))
        return bytes(c ^ k for c, k in zip(ciphertext, keystream))


class PydRuntimeProtector:
    """
    Creates protected Python files with a compiled .pyd runtime module.

    The protection works by:
    1. Compiling source to bytecode
    2. Encrypting the bytecode with AES-256-GCM
    3. Creating a Cython-compiled .pyd runtime that decrypts and executes

    Additional security features:
    - Anti-debugging detection
    - Time-based license expiration
    - Hardware/machine binding
    - Code integrity verification
    """

    MAGIC = b'PYD00003'  # Magic header for PYD-protected files (v3 = AES + advanced)
    VERSION = b'\x00\x03'

    def __init__(
        self,
        license_info: str = "PyObfuscate PYD Protection",
        encryption_key: Optional[bytes] = None,
        expiration_date: Optional[datetime] = None,
        allowed_machines: Optional[List[str]] = None,
        anti_debug: bool = True,
        domain_lock: Optional[List[str]] = None
    ):
        """
        Initialize the PydRuntimeProtector.

        Args:
            license_info: License/author information embedded in protected files
            encryption_key: Custom encryption key (32 bytes), or auto-generated
            expiration_date: Optional expiration date for the protected code
            allowed_machines: List of allowed machine IDs (use get_machine_id())
            anti_debug: Enable anti-debugging protection
            domain_lock: List of allowed domain names (for web apps)
        """
        self.license_info = license_info
        self.encryption_key = encryption_key or self._generate_key()
        self.crypto = CryptoEngine(self.encryption_key)
        self.runtime_id = self._generate_runtime_id()
        self.expiration_date = expiration_date
        self.allowed_machines = allowed_machines or []
        self.anti_debug = anti_debug
        self.domain_lock = domain_lock or []

    @staticmethod
    def get_machine_id() -> str:
        """
        Get a unique machine identifier for hardware binding.

        Returns:
            A hash of machine-specific information.
        """
        machine_info = []
        machine_info.append(platform.node())
        machine_info.append(platform.machine())
        machine_info.append(platform.processor())

        try:
            mac = uuid.getnode()
            if mac != uuid.getnode():
                mac = 0
            machine_info.append(str(mac))
        except:
            pass

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
            except:
                pass

        combined = '|'.join(machine_info)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _generate_key(self) -> bytes:
        """Generate a random encryption key."""
        return os.urandom(32)

    def _generate_runtime_id(self) -> str:
        """Generate a unique runtime identifier."""
        return hashlib.md5(self.encryption_key).hexdigest()[:6]

    def _compile_source(self, source: str, filename: str = '<protected>') -> bytes:
        """Compile Python source to bytecode."""
        code = compile(source, filename, 'exec')
        return marshal.dumps(code)

    def _create_payload(self, bytecode: bytes, metadata: Dict[str, Any]) -> bytes:
        """Create the encrypted payload with header."""
        compressed = zlib.compress(bytecode, level=9)
        meta_bytes = repr(metadata).encode('utf-8')
        meta_len = struct.pack('<H', len(meta_bytes))
        payload = meta_len + meta_bytes + compressed
        encrypted = self.crypto.encrypt(payload)
        data_len = struct.pack('<I', len(encrypted))
        checksum = hashlib.sha256(encrypted).digest()[:16]
        return self.MAGIC + self.VERSION + data_len + checksum + encrypted

    def protect_source(self, source: str, filename: str = '<protected>') -> Tuple[str, str, str]:
        """
        Protect Python source code.

        Returns:
            Tuple of (protected_code, cython_pyx_code, setup_py_code)
        """
        bytecode = self._compile_source(source, filename)

        metadata = {
            'created': datetime.now().isoformat(),
            'license': self.license_info,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'checksum': hashlib.sha256(source.encode()).hexdigest()[:16],
            'expiration': self.expiration_date.isoformat() if self.expiration_date else None,
            'machines': self.allowed_machines,
            'anti_debug': self.anti_debug,
            'domains': self.domain_lock,
        }

        payload = self._create_payload(bytecode, metadata)
        encoded_payload = base64.b64encode(payload).decode('ascii')

        protected_code = self._create_protected_file(encoded_payload, filename)
        pyx_code = self._create_cython_runtime()
        setup_code = self._create_setup_py()

        return protected_code, pyx_code, setup_code

    def _create_protected_file(self, encoded_payload: str, filename: str) -> str:
        """Create the protected Python file content."""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        return f'''# PyObfuscate 1.0.0 (PYD), {self.runtime_id}, {self.license_info}, {timestamp}
from pyobfuscate_runtime_{self.runtime_id} import __pyobfuscate__
__pyobfuscate__(__name__, __file__, b'{encoded_payload}')
'''

    def _create_cython_runtime(self) -> str:
        """Create the Cython .pyx file for compilation to .pyd with AES-256-GCM and advanced protection."""
        key_bytes = ', '.join(str(b) for b in self.encryption_key)

        return f'''# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# PyObfuscate PYD Runtime Module - {self.runtime_id}
# AES-256-GCM encryption with PBKDF2 key derivation
# Advanced protection: anti-debug, expiration, machine binding
# Compiled runtime for maximum protection

cimport cython
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.string cimport memcpy, memset

import base64
import hashlib
import hmac
import marshal
import os
import platform
import socket
import struct
import sys
import uuid
import zlib
from datetime import datetime

# Try to use cryptography library, fallback to pure Python
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

# Embedded encryption key (obfuscated in compiled binary)
cdef bytes _get_key():
    cdef unsigned char key_data[32]
    cdef list key_parts = [{key_bytes}]
    cdef int i
    for i in range(32):
        key_data[i] = key_parts[i]
    return bytes(key_data[:32])

cdef bytes _MAGIC = b'PYD00003'
cdef bytes _KEY = _get_key()
cdef int _SALT_SIZE = 16
cdef int _NONCE_SIZE = 12
cdef int _KEY_SIZE = 32
cdef int _ITERATIONS = 100000

# ============== Anti-Debugging ==============
cdef bint _check_debugger():
    """Detect if code is running under a debugger."""
    # Check sys.gettrace
    if sys.gettrace() is not None:
        return True
    
    # Check for debugger environment variables
    cdef list debug_vars = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL', 
                            'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT']
    for v in debug_vars:
        if os.environ.get(v):
            return True
    
    # Check for debugger modules
    cdef list debug_modules = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle']
    for dm in debug_modules:
        if dm in sys.modules:
            return True
    
    # Check frame inspection
    try:
        import inspect
        frame = inspect.currentframe()
        if frame:
            outer = frame.f_back
            while outer:
                code_name = outer.f_code.co_filename.lower()
                if any(dbg in code_name for dbg in ['pydevd', 'debugpy', 'pdb']):
                    return True
                outer = outer.f_back
    except:
        pass
    
    return False

# ============== Machine Binding ==============
cdef str _get_machine_id():
    """Get unique machine identifier."""
    cdef list info = []
    info.append(platform.node())
    info.append(platform.machine())
    info.append(platform.processor())
    try:
        mac = uuid.getnode()
        info.append(str(mac))
    except:
        pass
    if sys.platform == 'win32':
        try:
            import subprocess
            r = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'],
                              capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                lines = [l.strip() for l in r.stdout.split('\\n') 
                        if l.strip() and l.strip() != 'SerialNumber']
                if lines:
                    info.append(lines[0])
        except:
            pass
    return hashlib.sha256('|'.join(info).encode()).hexdigest()[:32]

# ============== Expiration Check ==============
cdef bint _check_expiration(str exp_str):
    """Check if the license has expired."""
    if not exp_str:
        return False
    try:
        exp = datetime.fromisoformat(exp_str)
        return datetime.now() > exp
    except:
        return False

# ============== Domain Lock ==============
cdef bint _check_domain(list domains):
    """Check if running on allowed domain."""
    if not domains:
        return True
    try:
        hostname = socket.gethostname().lower()
        fqdn = socket.getfqdn().lower()
        for d in domains:
            d = d.lower()
            if d in hostname or d in fqdn:
                return True
        return False
    except:
        return True

# ============== Crypto Functions ==============
cdef bytes _pbkdf2_sha256(bytes password, bytes salt, int iterations, int dklen):
    """Pure Python PBKDF2-HMAC-SHA256."""
    cdef bytes dk = b''
    cdef int block_num = 1
    cdef bytes u, result
    cdef int i
    
    while len(dk) < dklen:
        u = hmac.new(password, salt + struct.pack('>I', block_num), hashlib.sha256).digest()
        result = u
        for i in range(iterations - 1):
            u = hmac.new(password, u, hashlib.sha256).digest()
            result = bytes(x ^ y for x, y in zip(result, u))
        dk += result
        block_num += 1
    return dk[:dklen]

cdef bytes _derive_key(bytes key, bytes salt):
    """Derive decryption key using PBKDF2."""
    if _HAS_CRYPTO:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_SIZE,
            salt=salt,
            iterations=_ITERATIONS,
        )
        return kdf.derive(key)
    else:
        return _pbkdf2_sha256(key, salt, _ITERATIONS, _KEY_SIZE)

cdef bytes _generate_keystream(bytes key, bytes nonce, int length):
    """Generate keystream using counter mode."""
    cdef bytearray keystream = bytearray()
    cdef int counter = 0
    cdef bytes block_input, block
    
    while len(keystream) < length:
        block_input = key + nonce + struct.pack('<Q', counter)
        block = hashlib.sha256(block_input).digest()
        keystream.extend(block)
        counter += 1
    return bytes(keystream[:length])

@cython.boundscheck(False)
@cython.wraparound(False)  
cdef bytes _decrypt(bytes data, bytes master_key):
    """Decrypt AES-256-GCM encrypted data."""
    cdef bytes salt = data[:_SALT_SIZE]
    cdef bytes nonce = data[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    cdef bytes ciphertext = data[_SALT_SIZE + _NONCE_SIZE:]
    cdef bytes key = _derive_key(master_key, salt)
    cdef bytes auth_key, expected_tag, tag, ct, keystream
    cdef int i
    
    if _HAS_CRYPTO:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    else:
        # Fallback decryption with HMAC verification
        ct = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        auth_key = hashlib.sha256(key + b'auth').digest()
        expected_tag = hmac.new(auth_key, nonce + ct, hashlib.sha256).digest()[:16]
        
        if not hmac.compare_digest(tag, expected_tag):
            raise RuntimeError("Authentication failed - data corrupted or tampered")
        
        keystream = _generate_keystream(key, nonce, len(ct))
        return bytes(c ^ k for c, k in zip(ct, keystream))

# ============== Memory Protection ==============
cdef void _secure_clear(bytearray data):
    """Clear sensitive data from memory."""
    cdef int i
    for i in range(len(data)):
        data[i] = 0

# ============== Main Entry Point ==============
def __pyobfuscate__(name, file, payload):
    """Decrypt and execute protected code with security checks."""
    cdef bytes data, enc, dec, bc, meta_bytes
    cdef bytes chk, stored_chk
    cdef int dlen, mlen
    cdef bytearray key_copy = bytearray(_KEY)
    
    try:
        # Decode payload
        data = base64.b64decode(payload)
        
        # Verify magic header (support both v2 and v3)
        if data[:8] not in (b'PYD00002', b'PYD00003'):
            raise RuntimeError("Invalid protected file format")
        
        # Parse header
        dlen = struct.unpack('<I', data[10:14])[0]
        stored_chk = data[14:30]
        enc = data[30:30+dlen]
        
        # Verify checksum
        chk = hashlib.sha256(enc).digest()[:16]
        if chk != stored_chk:
            raise RuntimeError("Protected file corrupted or tampered")
        
        # Decrypt using AES-256-GCM
        dec = _decrypt(enc, bytes(key_copy))
        
        # Parse metadata and bytecode
        mlen = struct.unpack('<H', dec[:2])[0]
        meta_bytes = dec[2:2+mlen]
        meta = eval(meta_bytes.decode('utf-8'))
        bc = zlib.decompress(dec[2+mlen:])
        
        # ===== Security Checks =====
        
        # Anti-debugging check
        if meta.get('anti_debug', False) and _check_debugger():
            raise RuntimeError("Debugging detected - execution blocked")
        
        # Expiration check
        if _check_expiration(meta.get('expiration')):
            raise RuntimeError("License expired - please renew")
        
        # Machine binding check
        allowed = meta.get('machines', [])
        if allowed:
            current = _get_machine_id()
            if current not in allowed:
                raise RuntimeError(f"Machine not authorized. ID: {{current}}")
        
        # Domain lock check
        if not _check_domain(meta.get('domains', [])):
            raise RuntimeError("Domain not authorized")
        
        # ===== Execute Code =====
        # Load bytecode
        code = marshal.loads(bc)
        
        # Execute
        g = {{
            '__name__': name,
            '__file__': file,
            '__builtins__': __builtins__,
        }}
        
        exec(code, g)
        
        # Export to caller's module
        caller = sys.modules.get(name)
        if caller:
            for k, v in g.items():
                if not k.startswith('_'):
                    setattr(caller, k, v)
    
    finally:
        # Clear sensitive data
        _secure_clear(key_copy)
        del key_copy
'''

    def _create_setup_py(self) -> str:
        """Create the setup.py for building the .pyd."""
        return f'''# Setup script for building pyobfuscate_runtime_{self.runtime_id}.pyd
from setuptools import setup
from Cython.Build import cythonize
import sys

setup(
    name="pyobfuscate_runtime_{self.runtime_id}",
    ext_modules=cythonize(
        "pyobfuscate_runtime_{self.runtime_id}.pyx",
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
        }}
    ),
    zip_safe=False,
)
'''

    def build_pyd(
        self,
        output_dir: Path,
        cleanup: bool = True
    ) -> Optional[Path]:
        """
        Build the .pyd runtime module.

        Requires Cython and a C compiler to be installed.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create temp build directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write Cython source
            pyx_file = tmpdir / f"pyobfuscate_runtime_{self.runtime_id}.pyx"
            _, pyx_code, setup_code = self.protect_source("pass", "<dummy>")

            with open(pyx_file, 'w') as f:
                f.write(pyx_code)

            # Write setup.py
            setup_file = tmpdir / "setup.py"
            with open(setup_file, 'w') as f:
                f.write(setup_code)

            # Build the extension
            try:
                result = subprocess.run(
                    [sys.executable, "setup.py", "build_ext", "--inplace"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"Build failed: {{result.stderr}}")
                    return None

                # Find the built .pyd file
                for f in tmpdir.glob(f"pyobfuscate_runtime_{self.runtime_id}*.pyd"):
                    dest = output_dir / f.name
                    shutil.copy2(f, dest)
                    return dest

                # On Linux, look for .so file
                for f in tmpdir.glob(f"pyobfuscate_runtime_{self.runtime_id}*.so"):
                    dest = output_dir / f.name
                    shutil.copy2(f, dest)
                    return dest

            except Exception as e:
                print(f"Build error: {{e}}")
                return None

        return None

    def protect_file(
        self,
        input_path: Path,
        output_dir: Path,
        build_pyd: bool = True
    ) -> Dict[str, Any]:
        """
        Protect a Python file with PYD runtime.
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()

        protected, pyx, setup = self.protect_source(source, str(input_path))

        # Write protected file
        protected_path = output_dir / input_path.name
        with open(protected_path, 'w', encoding='utf-8') as f:
            f.write(protected)

        result = {
            'protected': protected_path,
            'pyx': None,
            'setup': None,
            'pyd': None
        }

        # Write Cython source (for manual building)
        pyx_path = output_dir / f"pyobfuscate_runtime_{self.runtime_id}.pyx"
        with open(pyx_path, 'w', encoding='utf-8') as f:
            f.write(pyx)
        result['pyx'] = pyx_path

        # Write setup.py
        setup_path = output_dir / "setup.py"
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(setup)
        result['setup'] = setup_path

        # Optionally build the .pyd
        if build_pyd:
            pyd_path = self.build_pyd(output_dir)
            result['pyd'] = pyd_path

        return result

    def protect_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[list] = None,
        build_pyd: bool = True
    ) -> Dict[str, Any]:
        """Protect all Python files in a directory."""
        import fnmatch

        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*']

        results = {'files': {}, 'pyd': None, 'pyx': None, 'setup': None}
        pattern = '**/*.py' if recursive else '*.py'
        first_file = True

        for py_file in input_dir.glob(pattern):
            relative = py_file.relative_to(input_dir)

            skip = False
            for excl in exclude_patterns:
                if fnmatch.fnmatch(str(relative), excl) or fnmatch.fnmatch(py_file.name, excl):
                    skip = True
                    break

            if skip:
                continue

            try:
                out_subdir = output_dir / relative.parent
                file_result = self.protect_file(
                    py_file,
                    out_subdir,
                    build_pyd=first_file and build_pyd
                )
                results['files'][str(relative)] = 'success'

                if first_file:
                    # Copy runtime files to output root
                    runtime_name = f'pyobfuscate_runtime_{self.runtime_id}'

                    if file_result['pyx']:
                        pyx_dest = output_dir / f'{runtime_name}.pyx'
                        if file_result['pyx'] != pyx_dest:
                            shutil.copy2(file_result['pyx'], pyx_dest)
                        results['pyx'] = pyx_dest

                    if file_result['setup']:
                        setup_dest = output_dir / 'setup.py'
                        if file_result['setup'] != setup_dest:
                            shutil.copy2(file_result['setup'], setup_dest)
                        results['setup'] = setup_dest

                    if file_result['pyd']:
                        pyd_dest = output_dir / file_result['pyd'].name
                        if file_result['pyd'] != pyd_dest:
                            shutil.copy2(file_result['pyd'], pyd_dest)
                        results['pyd'] = pyd_dest

                    first_file = False

            except Exception as e:
                results['files'][str(relative)] = f'error: {e}'

        return results

    def create_fallback_py_runtime(self, output_dir: Path) -> Path:
        """
        Create a pure Python fallback runtime (for when .pyd can't be built).
        Uses same AES-256-GCM encryption and security features as .pyd version.
        """
        output_dir = Path(output_dir)
        key_encoded = base64.b64encode(self.encryption_key).decode('ascii')

        runtime_code = f'''# PyObfuscate Runtime Module - {self.runtime_id}
# Pure Python fallback with AES-256-GCM encryption
# Advanced protection: anti-debug, expiration, machine binding
# Install cryptography package for better performance: pip install cryptography

import base64 as _b
import hashlib as _h
import hmac as _hm
import marshal as _m
import platform as _plat
import struct as _s
import sys as _sys
import uuid as _uuid
import zlib as _z
from datetime import datetime as _dt

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PBKDF2
    from cryptography.hazmat.primitives import hashes as _hashes
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

_MAGIC = b'PYD00003'
_KEY = _b.b64decode('{key_encoded}')
_SALT_SIZE = 16
_NONCE_SIZE = 12
_KEY_SIZE = 32
_ITERATIONS = 100000

# ============== Anti-Debugging ==============
def _check_debugger():
    if _sys.gettrace() is not None:
        return True
    import os as _os
    _debug_vars = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL', 'DEBUGPY_LAUNCHER_PORT']
    for _v in _debug_vars:
        if _os.environ.get(_v):
            return True
    _debug_modules = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle']
    for _dm in _debug_modules:
        if _dm in _sys.modules:
            return True
    return False

# ============== Machine Binding ==============
def _get_machine_id():
    _info = [_plat.node(), _plat.machine(), _plat.processor()]
    try:
        _info.append(str(_uuid.getnode()))
    except:
        pass
    if _sys.platform == 'win32':
        try:
            import subprocess as _sp
            _r = _sp.run(['wmic', 'diskdrive', 'get', 'serialnumber'], capture_output=True, text=True, timeout=5)
            if _r.returncode == 0:
                _lines = [l.strip() for l in _r.stdout.split('\\n') if l.strip() and l.strip() != 'SerialNumber']
                if _lines:
                    _info.append(_lines[0])
        except:
            pass
    return _h.sha256('|'.join(_info).encode()).hexdigest()[:32]

# ============== Expiration Check ==============
def _check_expiration(_exp_str):
    if not _exp_str:
        return False
    try:
        return _dt.now() > _dt.fromisoformat(_exp_str)
    except:
        return False

# ============== Domain Lock ==============
def _check_domain(_domains):
    if not _domains:
        return True
    try:
        import socket as _sock
        _hostname = _sock.gethostname().lower()
        _fqdn = _sock.getfqdn().lower()
        for _d in _domains:
            if _d.lower() in _hostname or _d.lower() in _fqdn:
                return True
        return False
    except:
        return True

# ============== Crypto Functions ==============
def _pbkdf2(_pw, _salt, _iters, _dklen):
    _dk = b''
    _bn = 1
    while len(_dk) < _dklen:
        _u = _hm.new(_pw, _salt + _s.pack('>I', _bn), _h.sha256).digest()
        _r = _u
        for _ in range(_iters - 1):
            _u = _hm.new(_pw, _u, _h.sha256).digest()
            _r = bytes(x ^ y for x, y in zip(_r, _u))
        _dk += _r
        _bn += 1
    return _dk[:_dklen]

def _derive(_k, _salt):
    if _HAS_CRYPTO:
        _kdf = _PBKDF2(algorithm=_hashes.SHA256(), length=_KEY_SIZE, salt=_salt, iterations=_ITERATIONS)
        return _kdf.derive(_k)
    return _pbkdf2(_k, _salt, _ITERATIONS, _KEY_SIZE)

def _keystream(_k, _n, _l):
    _ks = bytearray()
    _c = 0
    while len(_ks) < _l:
        _ks.extend(_h.sha256(_k + _n + _s.pack('<Q', _c)).digest())
        _c += 1
    return bytes(_ks[:_l])

def _decrypt(_d, _mk):
    _salt = _d[:_SALT_SIZE]
    _nonce = _d[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    _ct = _d[_SALT_SIZE + _NONCE_SIZE:]
    _k = _derive(_mk, _salt)
    if _HAS_CRYPTO:
        return _AESGCM(_k).decrypt(_nonce, _ct, None)
    _c = _ct[:-16]
    _tag = _ct[-16:]
    _ak = _h.sha256(_k + b'auth').digest()
    _et = _hm.new(_ak, _nonce + _c, _h.sha256).digest()[:16]
    if not _hm.compare_digest(_tag, _et):
        raise RuntimeError("Authentication failed - data corrupted or tampered")
    _ks = _keystream(_k, _nonce, len(_c))
    return bytes(c ^ k for c, k in zip(_c, _ks))

def _secure_clear(_data):
    if isinstance(_data, bytearray):
        for _i in range(len(_data)):
            _data[_i] = 0

def __pyobfuscate__(_name, _file, _payload):
    _data = _b.b64decode(_payload)
    _key_copy = bytearray(_KEY)
    
    try:
        # Verify magic header (support both v2 and v3)
        if _data[:8] not in (b'PYD00002', b'PYD00003'):
            raise RuntimeError("Invalid protected file format")
        _dlen = _s.unpack('<I', _data[10:14])[0]
        _chk = _data[14:30]
        _enc = _data[30:30+_dlen]
        if _h.sha256(_enc).digest()[:16] != _chk:
            raise RuntimeError("Protected file corrupted or tampered")
        _dec = _decrypt(_enc, bytes(_key_copy))
        
        # Parse metadata
        _mlen = _s.unpack('<H', _dec[:2])[0]
        _meta_bytes = _dec[2:2+_mlen]
        _meta = eval(_meta_bytes.decode('utf-8'))
        _comp = _dec[2+_mlen:]
        
        # Security checks
        if _meta.get('anti_debug', False) and _check_debugger():
            raise RuntimeError("Debugging detected - execution blocked")
        if _check_expiration(_meta.get('expiration')):
            raise RuntimeError("License expired - please renew")
        _allowed = _meta.get('machines', [])
        if _allowed:
            _current = _get_machine_id()
            if _current not in _allowed:
                raise RuntimeError(f"Machine not authorized. ID: {{_current}}")
        if not _check_domain(_meta.get('domains', [])):
            raise RuntimeError("Domain not authorized")
        
        # Execute
        _bc = _z.decompress(_comp)
        _code = _m.loads(_bc)
        _g = {{'__name__': _name, '__file__': _file, '__builtins__': __builtins__}}
        exec(_code, _g)
        _caller = _sys.modules.get(_name)
        if _caller:
            for _k, _v in _g.items():
                if not _k.startswith('_'):
                    setattr(_caller, _k, _v)
    finally:
        _secure_clear(_key_copy)
        del _key_copy
'''
        runtime_path = output_dir / f'pyobfuscate_runtime_{self.runtime_id}.py'
        with open(runtime_path, 'w', encoding='utf-8') as f:
            f.write(runtime_code)
        return runtime_path
