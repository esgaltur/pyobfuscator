"""
Runtime Protection Module - Similar to PyArmor's approach.

This creates encrypted Python files that require a runtime module to execute.
The code is compiled to bytecode, encrypted, and wrapped in a loader.

Uses AES-256-GCM encryption with PBKDF2 key derivation for strong protection.

Features:
- AES-256-GCM encryption with PBKDF2 key derivation
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
import random
import struct
import sys
import uuid
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

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

    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32
    ITERATIONS = 100000

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


class RuntimeProtector:
    """
    Creates PyArmor-style protected Python files.

    The protection works by:
    1. Compiling source to bytecode
    2. Encrypting the bytecode with AES-256-GCM
    3. Creating a loader that decrypts and executes at runtime

    Additional security features:
    - Anti-debugging detection
    - Time-based license expiration
    - Hardware/machine binding
    - Code integrity verification
    """

    MAGIC = b'PYO00003'  # Magic header (v3 = AES encryption + advanced protection)
    VERSION = b'\x00\x03'

    def __init__(
        self,
        license_info: str = "PyObfuscate Runtime Protection",
        encryption_key: Optional[bytes] = None,
        expiration_date: Optional[datetime] = None,
        allowed_machines: Optional[List[str]] = None,
        anti_debug: bool = True,
        domain_lock: Optional[List[str]] = None
    ):
        """
        Initialize the RuntimeProtector.

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
        except:
            pass

        # Try to get disk serial (Windows)
        if sys.platform == 'win32':
            try:
                import subprocess
                result = subprocess.run(
                    ['wmic', 'diskdrive', 'get', 'serialnumber'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and l.strip() != 'SerialNumber']
                    if lines:
                        machine_info.append(lines[0])
            except:
                pass

        # Create hash
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
        # Compress the bytecode
        compressed = zlib.compress(bytecode, level=9)

        # Create metadata
        meta_bytes = repr(metadata).encode('utf-8')
        meta_len = struct.pack('<H', len(meta_bytes))

        # Encrypt everything
        payload = meta_len + meta_bytes + compressed
        encrypted = self.crypto.encrypt(payload)

        # Add header
        data_len = struct.pack('<I', len(encrypted))
        checksum = hashlib.sha256(encrypted).digest()[:16]

        return self.MAGIC + self.VERSION + data_len + checksum + encrypted

    def protect_source(self, source: str, filename: str = '<protected>') -> Tuple[str, str]:
        """
        Protect Python source code.

        Returns:
            Tuple of (protected_code, runtime_module_code)
        """
        # Compile to bytecode
        bytecode = self._compile_source(source, filename)

        # Create metadata with protection settings
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

        # Create encrypted payload
        payload = self._create_payload(bytecode, metadata)

        # Base64 encode for embedding in source
        encoded_payload = base64.b64encode(payload).decode('ascii')

        # Create the protected file
        protected_code = self._create_protected_file(encoded_payload, filename)

        # Create the runtime module
        runtime_code = self._create_runtime_module()

        return protected_code, runtime_code

    def _create_protected_file(self, encoded_payload: str, filename: str) -> str:
        """Create the protected Python file content."""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Break payload into chunks for readability (like PyArmor does)
        chunk_size = 76
        payload_lines = [encoded_payload[i:i+chunk_size]
                        for i in range(0, len(encoded_payload), chunk_size)]
        payload_str = "b'" + encoded_payload + "'"

        return f'''# PyObfuscate 1.0.0, {self.runtime_id}, {self.license_info}, {timestamp}
from pyobfuscate_runtime_{self.runtime_id} import __pyobfuscate__
__pyobfuscate__(__name__, __file__, {payload_str})
'''

    def _create_runtime_module(self) -> str:
        """Create the runtime decryption module with AES-256-GCM and advanced protection."""
        key_encoded = base64.b64encode(self.encryption_key).decode('ascii')

        return f'''# PyObfuscate Runtime Module - {self.runtime_id}
# AES-256-GCM encryption with PBKDF2 key derivation
# Advanced protection: anti-debug, expiration, machine binding
# DO NOT MODIFY - Required for protected code execution

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

_MAGIC = b'PYO00003'
_KEY = _b.b64decode('{key_encoded}')
_SALT_SIZE = 16
_NONCE_SIZE = 12
_KEY_SIZE = 32
_ITERATIONS = 100000

# ============== Anti-Debugging ==============
def _check_debugger():
    """Detect if code is running under a debugger."""
    # Check sys.gettrace (debuggers like pdb set this)
    if _sys.gettrace() is not None:
        return True
    
    # Check for common debugger environment variables
    import os as _os
    _debug_vars = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL', 
                   'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT']
    for _v in _debug_vars:
        if _os.environ.get(_v):
            return True
    
    # Check for debugger modules
    _debug_modules = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle']
    for _dm in _debug_modules:
        if _dm in _sys.modules:
            return True
    
    # Check frame inspection (may indicate inspection tools)
    try:
        import inspect as _inspect
        _frame = _inspect.currentframe()
        if _frame:
            _outer = _frame.f_back
            while _outer:
                _code_name = _outer.f_code.co_filename.lower()
                if any(_dbg in _code_name for _dbg in ['pydevd', 'debugpy', 'pdb']):
                    return True
                _outer = _outer.f_back
    except:
        pass
    
    return False

# ============== Machine Binding ==============
def _get_machine_id():
    """Get unique machine identifier."""
    _info = []
    _info.append(_plat.node())
    _info.append(_plat.machine())
    _info.append(_plat.processor())
    try:
        _mac = _uuid.getnode()
        _info.append(str(_mac))
    except:
        pass
    if _sys.platform == 'win32':
        try:
            import subprocess as _sp
            _r = _sp.run(['wmic', 'diskdrive', 'get', 'serialnumber'],
                        capture_output=True, text=True, timeout=5)
            if _r.returncode == 0:
                _lines = [l.strip() for l in _r.stdout.split('\\n') 
                         if l.strip() and l.strip() != 'SerialNumber']
                if _lines:
                    _info.append(_lines[0])
        except:
            pass
    return _h.sha256('|'.join(_info).encode()).hexdigest()[:32]

# ============== Expiration Check ==============
def _check_expiration(_exp_str):
    """Check if the license has expired."""
    if not _exp_str:
        return False
    try:
        _exp = _dt.fromisoformat(_exp_str)
        return _dt.now() > _exp
    except:
        return False

# ============== Domain Lock ==============
def _check_domain(_domains):
    """Check if running on allowed domain (for web apps)."""
    if not _domains:
        return True
    try:
        import socket as _sock
        _hostname = _sock.gethostname().lower()
        _fqdn = _sock.getfqdn().lower()
        for _d in _domains:
            _d = _d.lower()
            if _d in _hostname or _d in _fqdn:
                return True
        return False
    except:
        return True  # Allow if can't check

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

# ============== Memory Protection ==============
def _secure_clear(_data):
    """Attempt to clear sensitive data from memory."""
    if isinstance(_data, bytearray):
        for _i in range(len(_data)):
            _data[_i] = 0
    elif isinstance(_data, memoryview):
        _data[:] = b'\\x00' * len(_data)

# ============== Main Entry Point ==============
def __pyobfuscate__(_name, _file, _payload):
    """Decrypt and execute protected code with security checks."""
    _data = _b.b64decode(_payload)
    _key_copy = bytearray(_KEY)
    
    try:
        # Verify magic header (support both v2 and v3)
        if _data[:8] not in (b'PYO00002', b'PYO00003'):
            raise RuntimeError("Invalid protected file format")
        
        _dlen = _s.unpack('<I', _data[10:14])[0]
        _chk = _data[14:30]
        _enc = _data[30:30+_dlen]
        
        if _h.sha256(_enc).digest()[:16] != _chk:
            raise RuntimeError("Protected file corrupted or tampered")
        
        # Decrypt
        _dec = _decrypt(_enc, bytes(_key_copy))
        
        # Parse metadata
        _mlen = _s.unpack('<H', _dec[:2])[0]
        _meta_bytes = _dec[2:2+_mlen]
        _meta = eval(_meta_bytes.decode('utf-8'))
        _comp = _dec[2+_mlen:]
        
        # ===== Security Checks =====
        
        # Anti-debugging check
        if _meta.get('anti_debug', False) and _check_debugger():
            raise RuntimeError("Debugging detected - execution blocked")
        
        # Expiration check
        if _check_expiration(_meta.get('expiration')):
            raise RuntimeError("License expired - please renew")
        
        # Machine binding check
        _allowed = _meta.get('machines', [])
        if _allowed:
            _current = _get_machine_id()
            if _current not in _allowed:
                raise RuntimeError(f"Machine not authorized. ID: {{_current}}")
        
        # Domain lock check
        if not _check_domain(_meta.get('domains', [])):
            raise RuntimeError("Domain not authorized")
        
        # ===== Execute Code =====
        _bc = _z.decompress(_comp)
        _code = _m.loads(_bc)
        
        _g = {{
            '__name__': _name,
            '__file__': _file,
            '__builtins__': __builtins__,
        }}
        
        exec(_code, _g)
        
        # Copy exports to caller's namespace
        _caller = _sys.modules.get(_name)
        if _caller:
            for _k, _v in _g.items():
                if not _k.startswith('_'):
                    setattr(_caller, _k, _v)
    
    finally:
        # Clear sensitive data
        _secure_clear(_key_copy)
        del _key_copy
'''

    def protect_file(
        self,
        input_path: Path,
        output_dir: Path,
        create_runtime: bool = True
    ) -> Dict[str, Path]:
        """
        Protect a Python file.

        Args:
            input_path: Path to the source file
            output_dir: Directory for output files
            create_runtime: Whether to create the runtime module

        Returns:
            Dict with paths to created files
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read source
        with open(input_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Protect
        protected, runtime = self.protect_source(source, str(input_path))

        # Write protected file
        protected_path = output_dir / input_path.name
        with open(protected_path, 'w', encoding='utf-8') as f:
            f.write(protected)

        result = {'protected': protected_path}

        # Write runtime module
        if create_runtime:
            runtime_path = output_dir / f'pyobfuscate_runtime_{self.runtime_id}.py'
            with open(runtime_path, 'w', encoding='utf-8') as f:
                f.write(runtime)
            result['runtime'] = runtime_path

        return result

    def protect_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Protect all Python files in a directory.
        """
        import fnmatch

        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*']

        results = {'files': {}, 'runtime': None}
        pattern = '**/*.py' if recursive else '*.py'
        runtime_created = False

        for py_file in input_dir.glob(pattern):
            relative = py_file.relative_to(input_dir)

            # Check exclusions
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
                    create_runtime=not runtime_created
                )
                results['files'][str(relative)] = 'success'

                if not runtime_created and 'runtime' in file_result:
                    # Copy runtime to output root
                    runtime_name = f'pyobfuscate_runtime_{self.runtime_id}.py'
                    runtime_dest = output_dir / runtime_name
                    if file_result['runtime'] != runtime_dest:
                        import shutil
                        shutil.copy2(file_result['runtime'], runtime_dest)
                    results['runtime'] = runtime_dest
                    runtime_created = True

            except Exception as e:
                results['files'][str(relative)] = f'error: {e}'

        return results


def protect(
    source: str,
    license_info: str = "Protected",
    filename: str = "<protected>"
) -> Tuple[str, str]:
    """
    Convenience function to protect Python source code.

    Args:
        source: Python source code
        license_info: License/author information
        filename: Original filename (for error messages)

    Returns:
        Tuple of (protected_code, runtime_module_code)
    """
    protector = RuntimeProtector(license_info=license_info)
    return protector.protect_source(source, filename)
