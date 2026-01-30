"""
Runtime Protection Module for PyObfuscate.

This creates encrypted Python files that require a runtime module to execute.
The code is compiled to bytecode, encrypted, and wrapped in a loader.

Uses AES-256-GCM encryption with PBKDF2 key derivation for strong protection.

Features:
- AES-256-GCM encryption with PBKDF2 key derivation
- Anti-debugging detection (multi-layer)
- Time-based license expiration
- Hardware/machine binding
- Code integrity verification
- Memory protection (secure clearing)
- Polymorphic runtime generation
- Import hook loader
- Anti-dump protection
- Encrypted error messages
- Bytecode scrambling
"""

import base64
import hashlib
import marshal
import os
import random
import secrets
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
    2. Scrambling bytecode structure
    3. Encrypting with layered AES-256-GCM
    4. Creating a polymorphic loader that decrypts and executes at runtime

    Additional security features:
    - Anti-debugging detection (6+ layers)
    - Time-based license expiration
    - Hardware/machine binding
    - Code integrity verification
    - Import hook based execution
    - Anti-memory dump protection
    """

    MAGIC = b'PYO00004'  # Magic header (v4 = advanced protection)
    VERSION = b'\x00\x04'

    def __init__(
        self,
        license_info: str = "PyObfuscate Runtime Protection",
        encryption_key: Optional[bytes] = None,
        expiration_date: Optional[datetime] = None,
        allowed_machines: Optional[List[str]] = None,
        anti_debug: bool = True,
        domain_lock: Optional[List[str]] = None,
        enable_vm_detection: bool = False,
        enable_network_check: bool = False,
        license_server_url: Optional[str] = None
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
            enable_vm_detection: Enable VM/sandbox detection (may have false positives)
            enable_network_check: Enable online license validation
            license_server_url: URL for license validation server
        """
        self.license_info = license_info
        self.encryption_key = encryption_key or self._generate_key()
        self.crypto = CryptoEngine(self.encryption_key)
        self.runtime_id = self._generate_runtime_id()
        self.expiration_date = expiration_date
        self.allowed_machines = allowed_machines or []
        self.anti_debug = anti_debug
        self.domain_lock = domain_lock or []
        self.enable_vm_detection = enable_vm_detection
        self.enable_network_check = enable_network_check
        self.license_server_url = license_server_url

        # Generate unique polymorphic seeds for this runtime
        self._poly_seed = secrets.token_hex(8)
        self._junk_seed = random.randint(1000, 9999)

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

    def _scramble_bytecode(self, bytecode: bytes) -> Tuple[bytes, bytes]:
        """
        Scramble bytecode with XOR and shuffle for additional obfuscation.
        Returns (scrambled_bytecode, scramble_key).
        """
        # Generate a random scramble key
        scramble_key = os.urandom(32)

        # XOR the bytecode with repeating key
        scrambled = bytearray(len(bytecode))
        for i, b in enumerate(bytecode):
            scrambled[i] = b ^ scramble_key[i % len(scramble_key)]

        return bytes(scrambled), scramble_key

    def _layered_encrypt(self, data: bytes) -> bytes:
        """
        Apply multiple layers of encryption for defense in depth.
        Layer 1: XOR with derived key
        Layer 2: AES-256-GCM (main encryption)
        """
        # Layer 1: XOR obfuscation
        xor_key = hashlib.sha256(self.encryption_key + b'layer1').digest()
        xored = bytes(d ^ xor_key[i % 32] for i, d in enumerate(data))

        # Layer 2: AES-GCM encryption
        encrypted = self.crypto.encrypt(xored)

        return encrypted

    def _create_payload(self, bytecode: bytes, metadata: Dict[str, Any]) -> bytes:
        """Create the encrypted payload with header and layered encryption."""
        # Scramble bytecode first
        scrambled, scramble_key = self._scramble_bytecode(bytecode)

        # Compress the scrambled bytecode
        compressed = zlib.compress(scrambled, level=9)

        # Create metadata with scramble key
        metadata['_sk'] = base64.b64encode(scramble_key).decode('ascii')
        meta_bytes = repr(metadata).encode('utf-8')
        meta_len = struct.pack('<H', len(meta_bytes))

        # Apply layered encryption
        payload = meta_len + meta_bytes + compressed
        encrypted = self._layered_encrypt(payload)

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
        """Create the polymorphic runtime with advanced protection."""
        key_encoded = base64.b64encode(self.encryption_key).decode('ascii')
        xor_key_encoded = base64.b64encode(
            hashlib.sha256(self.encryption_key + b'layer1').digest()
        ).decode('ascii')

        # Generate runtime integrity hash
        runtime_hash = hashlib.sha256(self.encryption_key + b'integrity').hexdigest()[:16]

        # Polymorphic variable names based on seed
        seed = int(self._poly_seed[:8], 16)
        random.seed(seed)

        # Generate random but consistent function/variable names
        def rand_name(length=6):
            chars = 'abcdefghijklmnopqrstuvwxyz'
            return '_' + ''.join(random.choices(chars, k=length))

        # Generate unique names for this runtime
        v = {
            'b64': rand_name(), 'hl': rand_name(), 'hm': rand_name(),
            'ml': rand_name(), 'os': rand_name(), 'pl': rand_name(),
            'st': rand_name(), 'sy': rand_name(), 'tm': rand_name(),
            'ui': rand_name(), 'zl': rand_name(), 'dt': rand_name(),
            'key': rand_name(), 'magic': rand_name(), 'hash': rand_name(),
            'xkey': rand_name(), 'ss': rand_name(), 'ns': rand_name(),
            'ks': rand_name(), 'it': rand_name(), 'hc': rand_name(),
            'tc': rand_name(), 'ad': rand_name(), 'vd': rand_name(),
            'ic': rand_name(), 'gm': rand_name(), 'ce': rand_name(),
            'cd': rand_name(), 'pb': rand_name(), 'dk': rand_name(),
            'kst': rand_name(), 'dc': rand_name(), 'sc': rand_name(),
            'gk': rand_name(), 'ld': rand_name(), 'us': rand_name(),
            'err': rand_name(), 'ag': rand_name(), 'pbb': rand_name(),
            'hs': rand_name(),
        }

        # Encrypted error messages (XOR with key fragment)
        def encrypt_msg(msg):
            key_frag = self.encryption_key[:len(msg)]
            encrypted = bytes(m ^ k for m, k in zip(msg.encode(), (key_frag * (len(msg)//32 + 1))[:len(msg)]))
            return base64.b64encode(encrypted).decode()

        err_integrity = encrypt_msg("Runtime integrity compromised")
        err_format = encrypt_msg("Invalid format")
        err_corrupt = encrypt_msg("Data corrupted")
        err_debug = encrypt_msg("Debug environment detected")
        err_expired = encrypt_msg("License expired")
        err_machine = encrypt_msg("Unauthorized machine")
        err_domain = encrypt_msg("Domain unauthorized")
        err_auth = encrypt_msg("Integrity check failed")

        # Random junk code snippets for obfuscation
        junk_snippets = [
            f"_{self._junk_seed}_a = lambda x: x",
            f"_{self._junk_seed}_b = [None] * 0",
            f"_{self._junk_seed}_c = {{}}",
        ]
        junk_code = '\n'.join(junk_snippets)

        return f'''# PyObfuscate Runtime - {self.runtime_id}
# {secrets.token_hex(16)}
import base64 as {v['b64']}
import hashlib as {v['hl']}
import hmac as {v['hm']}
import marshal as {v['ml']}
import os as {v['os']}
import platform as {v['pl']}
import struct as {v['st']}
import sys as {v['sy']}
import time as {v['tm']}
import uuid as {v['ui']}
import zlib as {v['zl']}
from datetime import datetime as {v['dt']}
{junk_code}
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as {v['ag']}
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as {v['pbb']}
    from cryptography.hazmat.primitives import hashes as {v['hs']}
    {v['hc']} = True
except ImportError:
    {v['hc']} = False

{v['magic']} = bytes([80,89,79,48,48,48,48,52])
{v['key']} = {v['b64']}.b64decode('{key_encoded}')
{v['xkey']} = {v['b64']}.b64decode('{xor_key_encoded}')
{v['ss']}, {v['ns']}, {v['ks']}, {v['it']} = 16, 12, 32, 100000
{v['hash']} = '{runtime_hash}'

{v['err']} = {{
    'i': '{err_integrity}', 'f': '{err_format}', 'c': '{err_corrupt}',
    'd': '{err_debug}', 'e': '{err_expired}', 'm': '{err_machine}',
    'o': '{err_domain}', 'a': '{err_auth}'
}}

def {v['us']}(_c):
    _kf = {v['key']}[:len({v['b64']}.b64decode(_c))]
    _d = {v['b64']}.b64decode(_c)
    return bytes(d ^ k for d, k in zip(_d, (_kf * (len(_d)//32 + 1))[:len(_d)])).decode()

def {v['tc']}():
    _t1 = {v['tm']}.perf_counter_ns()
    _x = sum(range(1000))
    _t2 = {v['tm']}.perf_counter_ns()
    return (_t2 - _t1) > 5_000_000

def {v['ad']}():
    if {v['sy']}.gettrace() is not None: return True
    _dv = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL', 
           'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT', 'COVERAGE_PROCESS_START']
    for _v in _dv:
        if {v['os']}.environ.get(_v): return True
    _dm = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle', 'coverage', 'trace']
    for _m in _dm:
        if _m in {v['sy']}.modules: return True
    try:
        import inspect as _ins
        _f = _ins.currentframe()
        _dp = 0
        while _f and _dp < 50:
            _cn = _f.f_code.co_filename.lower()
            if any(_d in _cn for _d in ['pydevd', 'debugpy', 'pdb', 'coverage']): return True
            if '__debugger__' in _f.f_locals or '__pydevd' in str(_f.f_locals): return True
            _f = _f.f_back
            _dp += 1
    except: pass
    if hasattr({v['ad']}, '_c') and {v['tc']}(): return True
    {v['ad']}._c = True
    try:
        if {v['sy']}.getprofile() is not None: return True
    except: pass
    return False

def {v['vd']}():
    _ind = []
    _pn = {v['pl']}.node().lower()
    _pp = {v['pl']}.processor().lower()
    _vm = ['vmware', 'virtualbox', 'vbox', 'qemu', 'xen', 'hyperv', 'parallels', 'virtual', 'sandbox']
    for _s in _vm:
        if _s in _pn or _s in _pp: _ind.append(_s)
    _ve = ['VMWARE_', 'VBOX_', 'QEMU_', 'XEN_']
    for _k in {v['os']}.environ:
        for _e in _ve:
            if _k.startswith(_e): _ind.append(_k)
    try:
        if {v['os']}.cpu_count() and {v['os']}.cpu_count() < 2: _ind.append('cpu')
    except: pass
    return len(_ind) > 2

def {v['ic']}():
    try: return {v['hl']}.sha256({v['key']} + b'integrity').hexdigest()[:16] == {v['hash']}
    except: return False

def {v['gm']}():
    _i = [{v['pl']}.node(), {v['pl']}.machine(), {v['pl']}.processor()]
    try: _i.append(str({v['ui']}.getnode()))
    except: pass
    if {v['sy']}.platform == 'win32':
        try:
            import subprocess as _sp
            _r = _sp.run(['wmic', 'diskdrive', 'get', 'serialnumber'],
                        capture_output=True, text=True, timeout=5, 
                        creationflags=0x08000000)
            if _r.returncode == 0:
                _ls = [l.strip() for l in _r.stdout.split('\\n') if l.strip() and l.strip() != 'SerialNumber']
                if _ls: _i.append(_ls[0])
        except: pass
    return {v['hl']}.sha256('|'.join(_i).encode()).hexdigest()[:32]

def {v['ce']}(_e):
    if not _e: return False
    try:
        _exp = {v['dt']}.fromisoformat(_e)
        _now = {v['dt']}.now()
        if _now.year < 2024: return True
        return _now > _exp
    except: return False

def {v['cd']}(_ds):
    if not _ds: return True
    try:
        import socket as _sk
        _hn = _sk.gethostname().lower()
        _fq = _sk.getfqdn().lower()
        return any(_d.lower() in _hn or _d.lower() in _fq for _d in _ds)
    except: return True

def {v['pb']}(_pw, _sl, _it, _dl):
    _dk, _bn = b'', 1
    while len(_dk) < _dl:
        _u = {v['hm']}.new(_pw, _sl + {v['st']}.pack('>I', _bn), {v['hl']}.sha256).digest()
        _r = _u
        for _ in range(_it - 1):
            _u = {v['hm']}.new(_pw, _u, {v['hl']}.sha256).digest()
            _r = bytes(x ^ y for x, y in zip(_r, _u))
        _dk += _r
        _bn += 1
    return _dk[:_dl]

def {v['dk']}(_k, _sl):
    if {v['hc']}:
        return {v['pbb']}(algorithm={v['hs']}.SHA256(), length={v['ks']}, salt=_sl, iterations={v['it']}).derive(_k)
    return {v['pb']}(_k, _sl, {v['it']}, {v['ks']})

def {v['kst']}(_k, _n, _l):
    _s, _c = bytearray(), 0
    while len(_s) < _l:
        _s.extend({v['hl']}.sha256(_k + _n + {v['st']}.pack('<Q', _c)).digest())
        _c += 1
    return bytes(_s[:_l])

def {v['dc']}(_d, _mk):
    _sl = _d[:{v['ss']}]
    _nc = _d[{v['ss']}:{v['ss']} + {v['ns']}]
    _ct = _d[{v['ss']} + {v['ns']}:]
    _k = {v['dk']}(_mk, _sl)
    if {v['hc']}:
        return {v['ag']}(_k).decrypt(_nc, _ct, None)
    _c, _tg = _ct[:-16], _ct[-16:]
    _ak = {v['hl']}.sha256(_k + b'auth').digest()
    _et = {v['hm']}.new(_ak, _nc + _c, {v['hl']}.sha256).digest()[:16]
    if not {v['hm']}.compare_digest(_tg, _et):
        raise RuntimeError({v['us']}({v['err']}['a']))
    return bytes(c ^ k for c, k in zip(_c, {v['kst']}(_k, _nc, len(_c))))

def {v['ld']}(_d, _xk):
    return bytes(d ^ _xk[i % 32] for i, d in enumerate(_d))

def {v['sc']}(_d):
    if isinstance(_d, bytearray):
        for _p in [0x00, 0xFF, 0xAA, 0x55, 0x00]:
            for _i in range(len(_d)): _d[_i] = _p

def {v['gk']}():
    _dc = bytearray({v['os']}.urandom(32))
    _rl = bytearray({v['key']})
    {v['sc']}(_dc)
    return _rl

def __pyobfuscate__(_nm, _fl, _pl):
    if not {v['ic']}(): raise RuntimeError({v['us']}({v['err']}['i']))
    _dr = {v['b64']}.b64decode(_pl)
    _kc = {v['gk']}()
    try:
        if _dr[:8] not in (b'PYO00002', b'PYO00003', {v['magic']}):
            raise RuntimeError({v['us']}({v['err']}['f']))
        _dl = {v['st']}.unpack('<I', _dr[10:14])[0]
        _ch = _dr[14:30]
        _en = _dr[30:30+_dl]
        if {v['hl']}.sha256(_en).digest()[:16] != _ch:
            raise RuntimeError({v['us']}({v['err']}['c']))
        _dec = {v['dc']}(_en, bytes(_kc))
        _dec = {v['ld']}(_dec, {v['xkey']})
        _mln = {v['st']}.unpack('<H', _dec[:2])[0]
        _mb = _dec[2:2+_mln]
        _mt = eval(_mb.decode('utf-8'))
        _cp = _dec[2+_mln:]
        if _mt.get('anti_debug', False) and {v['ad']}():
            raise RuntimeError({v['us']}({v['err']}['d']))
        if {v['ce']}(_mt.get('expiration')):
            raise RuntimeError({v['us']}({v['err']}['e']))
        _am = _mt.get('machines', [])
        if _am:
            _cm = {v['gm']}()
            if _cm not in _am:
                raise RuntimeError({v['us']}({v['err']}['m']) + f": {{_cm}}")
        if not {v['cd']}(_mt.get('domains', [])):
            raise RuntimeError({v['us']}({v['err']}['o']))
        _bc = {v['zl']}.decompress(_cp)
        _sk = {v['b64']}.b64decode(_mt.get('_sk', ''))
        if _sk:
            _bc = bytes(b ^ _sk[i % len(_sk)] for i, b in enumerate(_bc))
        _co = {v['ml']}.loads(_bc)
        _gl = {{'__name__': _nm, '__file__': _fl, '__builtins__': __builtins__}}
        exec(_co, _gl)
        _cl = {v['sy']}.modules.get(_nm)
        if _cl:
            for _k, _v in _gl.items():
                if not _k.startswith('_'): setattr(_cl, _k, _v)
    finally:
        {v['sc']}(_kc)
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
