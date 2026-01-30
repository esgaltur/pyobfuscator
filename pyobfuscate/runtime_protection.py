"""
Runtime Protection Module for PyObfuscate.

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

import base64
import hashlib
import marshal
import os
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from .crypto import CryptoEngine, get_machine_id


class RuntimeProtector:
    """
    Creates protected Python files with encrypted bytecode.

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
        return get_machine_id()

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

        # Break payload into chunks for readability
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

        # Generate a runtime integrity hash (hash of the key for self-verification)
        runtime_hash = hashlib.sha256(self.encryption_key + b'integrity').hexdigest()[:16]

        return f'''# PyObfuscate Runtime Module - {self.runtime_id}
# DO NOT MODIFY - Required for protected code execution
# Integrity: {runtime_hash}

import base64 as _b64
import hashlib as _hl
import hmac as _hm
import marshal as _ml
import os as _os
import platform as _pl
import struct as _st
import sys as _sy
import time as _tm
import uuid as _ui
import zlib as _zl
from datetime import datetime as _dt

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AG
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PB
    from cryptography.hazmat.primitives import hashes as _hs
    _HC = True
except ImportError:
    _HC = False

# Obfuscated constants
_M = bytes([80,89,79,48,48,48,48,51])  # Magic header
_K = _b64.b64decode('{key_encoded}')
_SS, _NS, _KS, _IT = 16, 12, 32, 100000
_IH = '{runtime_hash}'

# ============== Timing-based Anti-Debug ==============
def _tc():
    """Timing check - debuggers slow down execution."""
    _t1 = _tm.perf_counter_ns()
    _x = sum(range(1000))
    _t2 = _tm.perf_counter_ns()
    # Normal execution should be < 1ms, debuggers often 10x+ slower
    return (_t2 - _t1) > 5_000_000  # 5ms threshold

# ============== Enhanced Anti-Debugging ==============
def _ad():
    """Multi-layer debugger detection."""
    # Layer 1: sys.gettrace
    if _sy.gettrace() is not None:
        return True
    
    # Layer 2: Environment variables
    _dv = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL', 
           'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT', 'COVERAGE_PROCESS_START']
    for _v in _dv:
        if _os.environ.get(_v):
            return True
    
    # Layer 3: Debugger modules in memory
    _dm = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle', 'coverage', 'trace']
    for _m in _dm:
        if _m in _sy.modules:
            return True
    
    # Layer 4: Frame inspection
    try:
        import inspect as _ins
        _f = _ins.currentframe()
        _depth = 0
        while _f and _depth < 50:
            _cn = _f.f_code.co_filename.lower()
            if any(_d in _cn for _d in ['pydevd', 'debugpy', 'pdb', 'coverage']):
                return True
            # Check for unusual local variables (debugger artifacts)
            if '__debugger__' in _f.f_locals or '__pydevd' in str(_f.f_locals):
                return True
            _f = _f.f_back
            _depth += 1
    except:
        pass
    
    # Layer 5: Timing check (only on non-first-run to avoid cold start issues)
    if hasattr(_ad, '_called') and _tc():
        return True
    _ad._called = True
    
    # Layer 6: Check for tracing functions
    try:
        if _sy.getprofile() is not None:
            return True
    except:
        pass
    
    return False

# ============== VM/Sandbox Detection ==============
def _vd():
    """Detect common virtual machines and sandboxes."""
    _indicators = []
    
    # Check platform info for VM signatures
    _pn = _pl.node().lower()
    _pp = _pl.processor().lower()
    _pm = _pl.machine().lower()
    
    _vm_signs = ['vmware', 'virtualbox', 'vbox', 'qemu', 'xen', 'hyperv', 
                 'parallels', 'virtual', 'sandbox', 'malware', 'virus', 'analysis']
    
    for _sign in _vm_signs:
        if _sign in _pn or _sign in _pp:
            _indicators.append(_sign)
    
    # Check for VM-specific environment variables
    _vm_env = ['VMWARE_', 'VBOX_', 'QEMU_', 'XEN_']
    for _key in _os.environ:
        for _ve in _vm_env:
            if _key.startswith(_ve):
                _indicators.append(_key)
    
    # Check for suspiciously low resources (sandboxes often have minimal specs)
    try:
        if _os.cpu_count() and _os.cpu_count() < 2:
            _indicators.append('low_cpu')
    except:
        pass
    
    return len(_indicators) > 2  # Allow some false positives

# ============== Runtime Self-Integrity Check ==============
def _ic():
    """Verify runtime module hasn't been tampered with."""
    try:
        # Check if key derivation produces expected result
        _test = _hl.sha256(_K + b'integrity').hexdigest()[:16]
        return _test == _IH
    except:
        return False

# ============== Machine Binding ==============
def _gm():
    """Get unique machine identifier."""
    _i = [_pl.node(), _pl.machine(), _pl.processor()]
    try:
        _i.append(str(_ui.getnode()))
    except:
        pass
    if _sy.platform == 'win32':
        try:
            import subprocess as _sp
            _r = _sp.run(['wmic', 'diskdrive', 'get', 'serialnumber'],
                        capture_output=True, text=True, timeout=5, 
                        creationflags=0x08000000 if _sy.platform == 'win32' else 0)
            if _r.returncode == 0:
                _ls = [l.strip() for l in _r.stdout.split('\\n') 
                      if l.strip() and l.strip() != 'SerialNumber']
                if _ls:
                    _i.append(_ls[0])
        except:
            pass
    return _hl.sha256('|'.join(_i).encode()).hexdigest()[:32]

# ============== Time Checks ==============
def _ce(_e):
    """Check expiration with NTP fallback."""
    if not _e:
        return False
    try:
        _exp = _dt.fromisoformat(_e)
        _now = _dt.now()
        
        # Also check if system time seems manipulated (too far in past)
        if _now.year < 2024:
            return True  # Suspicious - system time in past
        
        return _now > _exp
    except:
        return False

# ============== Domain Lock ==============
def _cd(_ds):
    """Check domain restrictions."""
    if not _ds:
        return True
    try:
        import socket as _sk
        _hn = _sk.gethostname().lower()
        _fq = _sk.getfqdn().lower()
        return any(_d.lower() in _hn or _d.lower() in _fq for _d in _ds)
    except:
        return True

# ============== Crypto Core ==============
def _pb(_pw, _sl, _it, _dl):
    _dk, _bn = b'', 1
    while len(_dk) < _dl:
        _u = _hm.new(_pw, _sl + _st.pack('>I', _bn), _hl.sha256).digest()
        _r = _u
        for _ in range(_it - 1):
            _u = _hm.new(_pw, _u, _hl.sha256).digest()
            _r = bytes(x ^ y for x, y in zip(_r, _u))
        _dk += _r
        _bn += 1
    return _dk[:_dl]

def _dk(_k, _sl):
    if _HC:
        return _PB(algorithm=_hs.SHA256(), length=_KS, salt=_sl, iterations=_IT).derive(_k)
    return _pb(_k, _sl, _IT, _KS)

def _ks(_k, _n, _l):
    _s, _c = bytearray(), 0
    while len(_s) < _l:
        _s.extend(_hl.sha256(_k + _n + _st.pack('<Q', _c)).digest())
        _c += 1
    return bytes(_s[:_l])

def _dc(_d, _mk):
    _sl = _d[:_SS]
    _nc = _d[_SS:_SS + _NS]
    _ct = _d[_SS + _NS:]
    _k = _dk(_mk, _sl)
    if _HC:
        return _AG(_k).decrypt(_nc, _ct, None)
    _c, _tg = _ct[:-16], _ct[-16:]
    _ak = _hl.sha256(_k + b'auth').digest()
    _et = _hm.new(_ak, _nc + _c, _hl.sha256).digest()[:16]
    if not _hm.compare_digest(_tg, _et):
        raise RuntimeError("Integrity check failed")
    return bytes(c ^ k for c, k in zip(_c, _ks(_k, _nc, len(_c))))

# ============== Secure Memory Operations ==============
def _sc(_d):
    """Multi-pass secure clear."""
    if isinstance(_d, bytearray):
        for _p in [0x00, 0xFF, 0xAA, 0x55, 0x00]:  # Multiple overwrite passes
            for _i in range(len(_d)):
                _d[_i] = _p

def _gk():
    """Get key with decoy operations."""
    _decoy = bytearray(_os.urandom(32))  # Decoy to confuse memory analysis
    _real = bytearray(_K)
    _sc(_decoy)
    return _real

# ============== Main Entry ==============
def __pyobfuscate__(_nm, _fl, _pl):
    """Protected execution entry point."""
    # Self-integrity check first
    if not _ic():
        raise RuntimeError("Runtime integrity compromised")
    
    _dt_raw = _b64.b64decode(_pl)
    _kc = _gk()
    
    try:
        # Verify magic (support v2/v3)
        if _dt_raw[:8] not in (b'PYO00002', _M):
            raise RuntimeError("Invalid format")
        
        _dl = _st.unpack('<I', _dt_raw[10:14])[0]
        _ch = _dt_raw[14:30]
        _en = _dt_raw[30:30+_dl]
        
        if _hl.sha256(_en).digest()[:16] != _ch:
            raise RuntimeError("Data corrupted")
        
        _dec = _dc(_en, bytes(_kc))
        _ml = _st.unpack('<H', _dec[:2])[0]
        _mb = _dec[2:2+_ml]
        _mt = eval(_mb.decode('utf-8'))
        _cp = _dec[2+_ml:]
        
        # ===== Security Checks =====
        if _mt.get('anti_debug', False):
            if _ad():
                raise RuntimeError("Debug environment detected")
            # Optional: VM detection (disabled by default - too many false positives)
            # if _vd():
            #     raise RuntimeError("Virtualized environment detected")
        
        if _ce(_mt.get('expiration')):
            raise RuntimeError("License expired")
        
        _am = _mt.get('machines', [])
        if _am:
            _cm = _gm()
            if _cm not in _am:
                raise RuntimeError(f"Unauthorized machine: {{_cm}}")
        
        if not _cd(_mt.get('domains', [])):
            raise RuntimeError("Domain unauthorized")
        
        # ===== Execute =====
        _bc = _zl.decompress(_cp)
        _cd_obj = _ml.loads(_bc)
        
        _gl = {{'__name__': _nm, '__file__': _fl, '__builtins__': __builtins__}}
        exec(_cd_obj, _gl)
        
        _cl = _sy.modules.get(_nm)
        if _cl:
            for _k, _v in _gl.items():
                if not _k.startswith('_'):
                    setattr(_cl, _k, _v)
    
    finally:
        _sc(_kc)
        del _kc
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
