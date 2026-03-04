# -*- coding: utf-8 -*-
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

import base64
import hashlib
import marshal
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from .crypto import CryptoEngine, get_machine_id


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
    MAGIC_V2 = b'PYD00002'  # Legacy v2 magic for compatibility
    VERSION = b'\x00\x03'

    # Default filename constants
    DEFAULT_FILENAME = '<protected>'
    SETUP_PY_FILENAME = 'setup.py'

    # Error messages (centralized to avoid duplication)
    ERR_INVALID_FORMAT = "Invalid protected file format"
    ERR_CORRUPTED = "Protected file corrupted or tampered"
    ERR_AUTH_FAILED = "Authentication failed - data corrupted or tampered"
    ERR_DEBUG_DETECTED = "Debugging detected - execution blocked"
    ERR_LICENSE_EXPIRED = "License expired - please renew"
    ERR_MACHINE_UNAUTHORIZED = "Machine not authorized. ID: {machine_id}"
    ERR_DOMAIN_UNAUTHORIZED = "Domain not authorized"

    # Debug detection strings (centralized)
    DEBUG_ENV_VARS = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL',
                      'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT']
    DEBUG_MODULES = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle']
    DEBUG_FRAME_INDICATORS = ['pydevd', 'debugpy', 'pdb']

    # Machine ID constants
    WMIC_COMMAND = ['wmic', 'diskdrive', 'get', 'serialnumber']
    SERIAL_NUMBER_HEADER = 'SerialNumber'

    def __init__(
        self,
        license_info: str = "PyObfuscator PYD Protection",
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
        return get_machine_id()

    def _generate_key(self) -> bytes:
        """Generate a random encryption key."""
        return os.urandom(32)

    def _generate_runtime_id(self) -> str:
        """Generate a unique runtime identifier."""
        return hashlib.sha256(self.encryption_key).hexdigest()[:6]

    def _compile_source(self, source: str, filename: str = None) -> bytes:
        """Compile Python source to bytecode."""
        if filename is None:
            filename = self.DEFAULT_FILENAME
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

    def protect_source(self, source: str, filename: str = None) -> Tuple[str, str, str]:
        """
        Protect Python source code.

        Returns:
            Tuple of (protected_code, cython_pyx_code, setup_py_code)
        """
        if filename is None:
            filename = self.DEFAULT_FILENAME
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
        # Sanitize filename for comment (remove path, keep basename)
        safe_filename = Path(filename).name if filename else self.DEFAULT_FILENAME

        return f'''# PyObfuscator 2.0.0 (PYD), {self.runtime_id}, {self.license_info}, {timestamp}
# Source: {safe_filename}
from pyobfuscator_runtime_{self.runtime_id} import __pyobfuscator__
__pyobfuscator__(__name__, __file__, b'{encoded_payload}')
'''

    def _get_template_values(self) -> Dict[str, str]:
        """
        Get common template values used by both Cython and Python runtimes.


        Returns:
            Dict of template variable names to their repr() values
        """
        return {
            'debug_env_vars': repr(self.DEBUG_ENV_VARS),
            'debug_modules': repr(self.DEBUG_MODULES),
            'debug_frame_indicators': repr(self.DEBUG_FRAME_INDICATORS),
            'wmic_cmd': repr(self.WMIC_COMMAND),
            'serial_header': repr(self.SERIAL_NUMBER_HEADER),
            'err_invalid': repr(self.ERR_INVALID_FORMAT),
            'err_corrupted': repr(self.ERR_CORRUPTED),
            'err_auth': repr(self.ERR_AUTH_FAILED),
            'err_debug': repr(self.ERR_DEBUG_DETECTED),
            'err_expired': repr(self.ERR_LICENSE_EXPIRED),
            'err_domain': repr(self.ERR_DOMAIN_UNAUTHORIZED),
            'magic_v2': self.MAGIC_V2.decode(),
            'magic_v3': self.MAGIC.decode(),
            'runtime_id': self.runtime_id,
            'salt_size': '16',
            'nonce_size': '12',
            'key_size': '32',
            'iterations': '100000',
        }

    def _get_common_runtime_code(self, is_cython: bool = False) -> str:
        """
        Get the common runtime code shared between Cython and Python versions.

        Args:
            is_cython: If True, generate Cython-compatible code with cdef declarations

        Returns:
            Common runtime function implementations as a string
        """
        # Function signature prefix (cdef for Cython, def for Python)
        cdef_bint = "cdef bint " if is_cython else "def "
        cdef_str = "cdef str " if is_cython else "def "
        cdef_bytes = "cdef bytes " if is_cython else "def "
        cdef_void = "cdef void " if is_cython else "def "

        # Parameter type annotations (Cython uses type before param name, no cdef)
        param_str = "str " if is_cython else ""
        param_bytes = "bytes " if is_cython else ""
        param_list = "list " if is_cython else ""
        param_int = "int " if is_cython else ""

        # Local variable declarations (Cython needs 'cdef type var', Python uses plain assignment)
        # For Cython, we declare variables at the start of function body
        local_bytes = "cdef bytes " if is_cython else ""
        local_int = "cdef int " if is_cython else ""
        local_list = "cdef list " if is_cython else ""
        local_str = "cdef str " if is_cython else ""

        return f'''
# ============== Anti-Debugging ==============
{cdef_bint}_check_debugger():
    """Detect if code is running under a debugger."""
    if sys.gettrace() is not None:
        return True
    for v in _DEBUG_ENV_VARS:
        if os.environ.get(v):
            return True
    for dm in _DEBUG_MODULES:
        if dm in sys.modules:
            return True
    return False

# ============== Machine Binding ==============
{cdef_str}_get_machine_id():
    """Get unique machine identifier."""
    {local_list}info = []
    info.append(platform.node())
    info.append(platform.machine())
    info.append(platform.processor())
    try:
        info.append(str(uuid.getnode()))
    except:
        pass
    if sys.platform == 'win32':
        try:
            import subprocess
            r = subprocess.run(_WMIC_CMD, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                lines = [l.strip() for l in r.stdout.split('\\n') 
                        if l.strip() and l.strip() != _SERIAL_HEADER]
                if lines:
                    info.append(lines[0])
        except:
            pass
    return hashlib.sha256('|'.join(info).encode()).hexdigest()[:32]

# ============== Expiration Check ==============
{cdef_bint}_check_expiration({param_str}exp_str):
    """Check if the license has expired."""
    if not exp_str:
        return False
    try:
        exp = datetime.fromisoformat(exp_str)
        return datetime.now() > exp
    except:
        return False

# ============== Domain Lock ==============
{cdef_bint}_check_domain({param_list}domains):
    """Check if running on allowed domain."""
    {local_str}hostname, fqdn, d
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
{cdef_bytes}_pbkdf2_sha256({param_bytes}password, {param_bytes}salt, {param_int}iterations, {param_int}dklen):
    """Pure Python PBKDF2-HMAC-SHA256."""
    {local_bytes}dk, u, result
    {local_int}block_num
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

{cdef_bytes}_derive_key({param_bytes}key, {param_bytes}salt):
    """Derive decryption key using PBKDF2."""
    if _HAS_CRYPTO:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_SIZE,
            salt=salt,
            iterations=_ITERATIONS,
        )
        return kdf.derive(key)
    return _pbkdf2_sha256(key, salt, _ITERATIONS, _KEY_SIZE)

{cdef_bytes}_generate_keystream({param_bytes}key, {param_bytes}nonce, {param_int}length):
    """Generate keystream using counter mode."""
    {local_int}counter
    keystream = bytearray()
    counter = 0
    
    while len(keystream) < length:
        block = hashlib.sha256(key + nonce + struct.pack('<Q', counter)).digest()
        keystream.extend(block)
        counter += 1
    return bytes(keystream[:length])

{cdef_bytes}_decrypt({param_bytes}data, {param_bytes}master_key):
    """Decrypt AES-256-GCM encrypted data."""
    {local_bytes}salt, nonce, ciphertext, key, ct, tag, auth_key, expected_tag
    salt = data[:_SALT_SIZE]
    nonce = data[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    ciphertext = data[_SALT_SIZE + _NONCE_SIZE:]
    key = _derive_key(master_key, salt)
    
    if _HAS_CRYPTO:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    # Fallback decryption with HMAC verification
    ct = ciphertext[:-16]
    tag = ciphertext[-16:]
    
    auth_key = hashlib.sha256(key + b'auth').digest()
    expected_tag = hmac.new(auth_key, nonce + ct, hashlib.sha256).digest()[:16]
    
    if not hmac.compare_digest(tag, expected_tag):
        raise RuntimeError(_ERR_AUTH)
    
    keystream = _generate_keystream(key, nonce, len(ct))
    return bytes(c ^ k for c, k in zip(ct, keystream))

# ============== Memory Protection ==============
{cdef_void}_secure_clear(data):
    """Clear sensitive data from memory."""
    {local_int}i
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0
'''

    def _get_main_entry_code(self, is_cython: bool = False) -> str:
        """
        Get the main __pyobfuscator__ entry point code.

        Args:
            is_cython: If True, generate Cython-compatible code

        Returns:
            Main entry point function as a string
        """
        # Variable type declarations for Cython
        cdef_vars = """
    cdef bytes data, enc, dec, bc, meta_bytes
    cdef bytes chk, stored_chk
    cdef int dlen, mlen""" if is_cython else ""

        return f'''
# ============== Main Entry Point ==============
def __pyobfuscator__(name, file, payload):
    """Decrypt and execute protected code with security checks."""{cdef_vars}
    key_copy = bytearray(_KEY)
    
    try:
        # Decode payload
        data = base64.b64decode(payload)
        
        # Verify magic header (support both v2 and v3)
        if data[:8] not in (_MAGIC_V2, _MAGIC_V3):
            raise RuntimeError(_ERR_INVALID)
        
        # Parse header
        dlen = struct.unpack('<I', data[10:14])[0]
        stored_chk = data[14:30]
        enc = data[30:30+dlen]
        
        # Verify checksum
        chk = hashlib.sha256(enc).digest()[:16]
        if chk != stored_chk:
            raise RuntimeError(_ERR_CORRUPTED)
        
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
            raise RuntimeError(_ERR_DEBUG)
        
        # Expiration check
        if _check_expiration(meta.get('expiration')):
            raise RuntimeError(_ERR_EXPIRED)
        
        # Machine binding check
        allowed = meta.get('machines', [])
        if allowed:
            current = _get_machine_id()
            if current not in allowed:
                raise RuntimeError(f"Machine not authorized. ID: {{current}}")
        
        # Domain lock check
        if not _check_domain(meta.get('domains', [])):
            raise RuntimeError(_ERR_DOMAIN)
        
        # ===== Execute Code =====
        code = marshal.loads(bc)
        
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

    def _create_cython_runtime(self) -> str:
        """Create the Cython .pyx file for compilation to .pyd with AES-256-GCM and advanced protection."""
        key_bytes = ', '.join(str(b) for b in self.encryption_key)
        tv = self._get_template_values()

        # Get common code sections
        common_code = self._get_common_runtime_code(is_cython=True)
        main_entry = self._get_main_entry_code(is_cython=True)

        return f'''# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# PyObfuscator PYD Runtime Module - {tv['runtime_id']}
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

# Constants
cdef bytes _MAGIC_V2 = b'{tv['magic_v2']}'
cdef bytes _MAGIC_V3 = b'{tv['magic_v3']}'
cdef bytes _KEY = _get_key()
cdef int _SALT_SIZE = {tv['salt_size']}
cdef int _NONCE_SIZE = {tv['nonce_size']}
cdef int _KEY_SIZE = {tv['key_size']}
cdef int _ITERATIONS = {tv['iterations']}

# Error messages
cdef str _ERR_INVALID = {tv['err_invalid']}
cdef str _ERR_CORRUPTED = {tv['err_corrupted']}
cdef str _ERR_AUTH = {tv['err_auth']}
cdef str _ERR_DEBUG = {tv['err_debug']}
cdef str _ERR_EXPIRED = {tv['err_expired']}
cdef str _ERR_DOMAIN = {tv['err_domain']}

# Debug detection lists
cdef list _DEBUG_ENV_VARS = {tv['debug_env_vars']}
cdef list _DEBUG_MODULES = {tv['debug_modules']}
cdef list _DEBUG_FRAME_INDICATORS = {tv['debug_frame_indicators']}

# Machine ID constants
cdef list _WMIC_CMD = {tv['wmic_cmd']}
cdef str _SERIAL_HEADER = {tv['serial_header']}
{common_code}
{main_entry}
'''

    def _create_setup_py(self) -> str:
        """Create the setup.py for building the .pyd."""
        return f'''# Setup script for building pyobfuscator_runtime_{self.runtime_id}.pyd
from setuptools import setup
from Cython.Build import cythonize
import sys

setup(
    name="pyobfuscator_runtime_{self.runtime_id}",
    ext_modules=cythonize(
        "pyobfuscator_runtime_{self.runtime_id}.pyx",
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

        Args:
            output_dir: Directory to place the built .pyd file
            cleanup: If True, remove intermediate build files. If False, keep
                     the .pyx source and setup.py in output_dir for debugging.

        Returns:
            Path to the built .pyd/.so file, or None if build failed.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate runtime code
        _, pyx_code, setup_code = self.protect_source("pass", "<dummy>")

        # If not cleaning up, write files to output_dir for inspection
        if not cleanup:
            pyx_file = output_dir / f"pyobfuscator_runtime_{self.runtime_id}.pyx"
            setup_file = output_dir / self.SETUP_PY_FILENAME
            with open(pyx_file, 'w') as f:
                f.write(pyx_code)
            with open(setup_file, 'w') as f:
                f.write(setup_code)

        # Create temp build directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write Cython source
            pyx_file = tmpdir / f"pyobfuscator_runtime_{self.runtime_id}.pyx"

            with open(pyx_file, 'w') as f:
                f.write(pyx_code)

            # Write setup.py
            setup_file = tmpdir / self.SETUP_PY_FILENAME
            with open(setup_file, 'w') as f:
                f.write(setup_code)

            # Build the extension
            try:
                result = subprocess.run(
                    [sys.executable, self.SETUP_PY_FILENAME, "build_ext", "--inplace"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"Build failed: {result.stderr}")
                    return None

                # Find the built .pyd file
                for f in tmpdir.glob(f"pyobfuscator_runtime_{self.runtime_id}*.pyd"):
                    dest = output_dir / f.name
                    shutil.copy2(f, dest)
                    return dest

                # On Linux, look for .so file
                for f in tmpdir.glob(f"pyobfuscator_runtime_{self.runtime_id}*.so"):
                    dest = output_dir / f.name
                    shutil.copy2(f, dest)
                    return dest

            except Exception as e:
                print(f"Build error: {e}")
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
        pyx_path = output_dir / f"pyobfuscator_runtime_{self.runtime_id}.pyx"
        with open(pyx_path, 'w', encoding='utf-8') as f:
            f.write(pyx)
        result['pyx'] = pyx_path

        # Write setup.py
        setup_path = output_dir / self.SETUP_PY_FILENAME
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(setup)
        result['setup'] = setup_path

        # Optionally build the .pyd
        if build_pyd:
            pyd_path = self.build_pyd(output_dir)
            result['pyd'] = pyd_path

        return result

    def _should_skip_file(self, relative_path: Path, filename: str, exclude_patterns: list) -> bool:
        """Check if a file should be skipped based on exclude patterns."""
        import fnmatch
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str(relative_path), pattern):
                return True
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _copy_runtime_files(
        self,
        file_result: Dict[str, Any],
        output_dir: Path,
        results: Dict[str, Any]
    ) -> None:
        """Copy runtime files to output directory."""
        runtime_name = f'pyobfuscator_runtime_{self.runtime_id}'

        if file_result.get('pyx'):
            pyx_dest = output_dir / f'{runtime_name}.pyx'
            if file_result['pyx'] != pyx_dest:
                shutil.copy2(file_result['pyx'], pyx_dest)
            results['pyx'] = pyx_dest

        if file_result.get('setup'):
            setup_dest = output_dir / self.SETUP_PY_FILENAME
            if file_result['setup'] != setup_dest:
                shutil.copy2(file_result['setup'], setup_dest)
            results['setup'] = setup_dest

        if file_result.get('pyd'):
            pyd_dest = output_dir / file_result['pyd'].name
            if file_result['pyd'] != pyd_dest:
                shutil.copy2(file_result['pyd'], pyd_dest)
            results['pyd'] = pyd_dest

    def protect_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[list] = None,
        build_pyd: bool = True
    ) -> Dict[str, Any]:
        """Protect all Python files in a directory."""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*']

        results: Dict[str, Any] = {'files': {}, 'pyd': None, 'pyx': None, 'setup': None}
        pattern = '**/*.py' if recursive else '*.py'
        first_file = True

        for py_file in input_dir.glob(pattern):
            relative = py_file.relative_to(input_dir)

            if self._should_skip_file(relative, py_file.name, exclude_patterns):
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
                    self._copy_runtime_files(file_result, output_dir, results)
                    first_file = False

            except Exception as e:
                results['files'][str(relative)] = f'error: {e}'

        return results

    def create_fallback_py_runtime(self, output_dir: Path) -> Path:
        """
        Create a pure Python fallback runtime (for when .pyd can't be built).
        Uses the same AES-256-GCM encryption and security features as the.pyd version.
        """
        output_dir = Path(output_dir)
        key_encoded = base64.b64encode(self.encryption_key).decode('ascii')
        tv = self._get_template_values()

        # Get common code sections (Python version - no cdef)
        common_code = self._get_common_runtime_code(is_cython=False)
        main_entry = self._get_main_entry_code(is_cython=False)

        runtime_code = f'''# PyObfuscator Runtime Module - {tv['runtime_id']}
# Pure Python fallback with AES-256-GCM encryption
# Advanced protection: anti-debug, expiration, machine binding
# Install cryptography package for better performance: pip install cryptography

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

# Constants
_MAGIC_V2 = b'{tv['magic_v2']}'
_MAGIC_V3 = b'{tv['magic_v3']}'
_KEY = base64.b64decode('{key_encoded}')
_SALT_SIZE = {tv['salt_size']}
_NONCE_SIZE = {tv['nonce_size']}
_KEY_SIZE = {tv['key_size']}
_ITERATIONS = {tv['iterations']}

# Error messages
_ERR_INVALID = {tv['err_invalid']}
_ERR_CORRUPTED = {tv['err_corrupted']}
_ERR_AUTH = {tv['err_auth']}
_ERR_DEBUG = {tv['err_debug']}
_ERR_EXPIRED = {tv['err_expired']}
_ERR_DOMAIN = {tv['err_domain']}

# Debug detection
_DEBUG_ENV_VARS = {tv['debug_env_vars']}
_DEBUG_MODULES = {tv['debug_modules']}

# Machine ID
_WMIC_CMD = {tv['wmic_cmd']}
_SERIAL_HEADER = {tv['serial_header']}
{common_code}
{main_entry}
'''
        runtime_path = output_dir / f'pyobfuscator_runtime_{self.runtime_id}.py'
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(runtime_path, 'w', encoding='utf-8') as f:
            f.write(runtime_code)
        return runtime_path
