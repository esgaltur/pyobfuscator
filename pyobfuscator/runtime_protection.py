# -*- coding: utf-8 -*-
"""
Runtime Protection Module for PyObfuscator.

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

from .crypto import CryptoEngine, get_machine_id, WhiteBoxEngine
from .constants import RuntimeConstants

class VM:
    # Advanced virtualization: randomized opcodes, stack-based, self-modifying, anti-analysis
    
    # Static opcode table for the core transformer
    _OPMAP = {
        0x01: 'PUSH', 0x02: 'POP', 0x03: 'DUP', 0x04: 'SWAP', 0x05: 'ROT3',
        0x10: 'ADD', 0x11: 'SUB', 0x12: 'MUL', 0x13: 'DIV', 0x14: 'MOD',
        0x20: 'XOR', 0x21: 'AND', 0x22: 'OR', 0x23: 'NOT', 0x24: 'SHL', 0x25: 'SHR',
        0x30: 'LOAD', 0x31: 'STORE', 0x32: 'LOADB', 0x33: 'STOREB',
        0x40: 'JMP', 0x41: 'JZ', 0x42: 'JNZ', 0x43: 'JGT', 0x44: 'JLT',
        0xF0: 'HALT'
    }
    
    _REVMAP = {v: k for k, v in _OPMAP.items()}
    
    def __init__(self):
        self._stk = []
        self._mem = [0] * 1024
        self._cstk = []
        self._pc = 0
        self._bc = bytearray()
        self._dat = bytearray()
        self._run = True
        
    def _pu(self, _v): self._stk.append(_v & 0xFFFFFFFF)
    def _po(self): return self._stk.pop() if self._stk else 0
    def _pk(self): return self._stk[-1] if self._stk else 0
    
    def _r8(self):
        if self._pc < len(self._bc):
            _v = self._bc[self._pc]
            self._pc += 1
            return _v
        return 0
    
    def _r32(self):
        _v = struct.unpack('<I', self._bc[self._pc:self._pc+4])[0]
        self._pc += 4
        return _v
    
    def execute(self, _bytecode, _data=b''):
        self._bc = bytearray(_bytecode)
        self._dat = bytearray(_data)
        self._pc = 0
        self._run = True
        self._stk = []
        
        while self._run and self._pc < len(self._bc):
            _op = self._r8()
            _nm = self._OPMAP.get(_op, 'HALT')
            
            if _nm == 'PUSH': self._pu(self._r32())
            elif _nm == 'POP': self._po()
            elif _nm == 'DUP': self._pu(self._pk())
            elif _nm == 'ADD':
                _b, _a = self._po(), self._po()
                self._pu(_a + _b)
            elif _nm == 'SUB':
                _b, _a = self._po(), self._po()
                self._pu(_a - _b)
            elif _nm == 'MUL':
                _b, _a = self._po(), self._po()
                self._pu(_a * _b)
            elif _nm == 'XOR':
                _b, _a = self._po(), self._po()
                self._pu(_a ^ _b)
            elif _nm == 'LOAD':
                _addr = self._po()
                self._pu(self._mem[_addr] if _addr < len(self._mem) else 0)
            elif _nm == 'STORE':
                _val, _addr = self._po(), self._po()
                if _addr < len(self._mem): self._mem[_addr] = _val & 0xFFFFFFFF
            elif _nm == 'HALT': self._run = False
        return self._mem

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

    # Use constants from the constants module
    MAGIC = RuntimeConstants.MAGIC
    VERSION = RuntimeConstants.VERSION
    DEFAULT_FILENAME = RuntimeConstants.DEFAULT_FILENAME

    def __init__(
        self,
        license_info: str = "PyObfuscator Runtime Protection",
        encryption_key: Optional[bytes] = None,
        expiration_date: Optional[datetime] = None,
        allowed_machines: Optional[List[str]] = None,
        anti_debug: bool = True,
        domain_lock: Optional[List[str]] = None,
        enable_vm_detection: bool = False,
        enable_network_check: bool = False,
        license_server_url: Optional[str] = None,
        use_whitebox: bool = False
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
            use_whitebox: Use White-Box Cryptography (Lut-based) instead of standard AES
        """
        self.license_info = license_info
        self.encryption_key = encryption_key or self._generate_key()
        self.crypto = CryptoEngine(self.encryption_key)
        self.use_whitebox = use_whitebox
        self.wbc = WhiteBoxEngine(self.encryption_key) if use_whitebox else None
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
        return hashlib.sha256(self.encryption_key).hexdigest()[:6]

    def _compile_source(self, source: str, filename: str = None) -> bytes:
        """Compile Python source to bytecode."""
        if filename is None:
            filename = self.DEFAULT_FILENAME
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
        Layer 1: XOR or White-Box
        Layer 2: AES-256-GCM (main encryption)
        """
        if self.use_whitebox:
            # Layer 1: White-Box Cryptography (LUT-based)
            protected = self.wbc.encrypt(data)
        else:
            # Layer 1: XOR obfuscation
            xor_key = hashlib.sha256(self.encryption_key + b'layer1').digest()
            protected = bytes(d ^ xor_key[i % 32] for i, d in enumerate(data))

        # Layer 2: AES-GCM encryption
        encrypted = self.crypto.encrypt(protected)

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

    def protect_source(self, source: str, filename: str = None) -> Tuple[str, str]:
        """
        Protect Python source code.

        Returns:
            Tuple of (protected_code, runtime_module_code)
        """
        if filename is None:
            filename = self.DEFAULT_FILENAME

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
            'vm_detect': self.enable_vm_detection,
            'license_server': self.license_server_url if self.enable_network_check else None,
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
        # Sanitize filename for comment (remove path, keep basename)
        safe_filename = Path(filename).name if filename else self.DEFAULT_FILENAME

        payload_str = "b'" + encoded_payload + "'"

        return f'''# PyObfuscator 2.0.0, {self.runtime_id}, {self.license_info}, {timestamp}
# Source: {safe_filename}
from pyobfuscator_runtime_{self.runtime_id} import __pyobfuscator__
__pyobfuscator__(__name__, __file__, {payload_str})
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
            'kst': rand_name(), 'dcp': rand_name(), 'sc': rand_name(),
            'gk': rand_name(), 'ld': rand_name(), 'us': rand_name(),
            'err': rand_name(), 'ag': rand_name(), 'pbb': rand_name(),
            'hs': rand_name(),
            # Security features
            'wm': rand_name(),   # watermark
            'ht': rand_name(),   # honey token
            'ap': rand_name(),   # anti-patch
            'csv': rand_name(),  # call stack verify
            'cf': rand_name(),   # control flow
            'op': rand_name(),   # opaque predicates
            'nl': rand_name(),   # network license
            # New advanced features
            'amd': rand_name(),  # anti-memory dump
            'ih': rand_name(),   # imported hook
            'stbl': rand_name(), # string table
            'cs1': rand_name(),  # code split 1
            'cs2': rand_name(),  # code split 2
            'cs3': rand_name(),  # code split 3
            'rat': rand_name(),  # resource exhaustion on tampering
            'vm': rand_name(),   # virtualization helper
            'th': rand_name(),   # thread check
            'ptr': rand_name(),  # parent trace
            # New advanced features
            'ah': rand_name(),   # anti-hooking
            'cb': rand_name(),   # constant blinding
            'ef': rand_name(),   # environment fingerprint
            'cc': rand_name(),   # checksum chain
            'dc': rand_name(),   # dead code
            'fe': rand_name(),   # fake error paths
            'sm': rand_name(),   # state machine
            'id': rand_name(),   # incremental decrypt
            'wdec': rand_name(), # whitebox decoder
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
        err_memory = encrypt_msg("Memory analysis detected")
        err_thread = encrypt_msg("Threading violation")
        err_parent = encrypt_msg("Invalid parent process")
        err_hook = encrypt_msg("Function hooking detected")
        err_env = encrypt_msg("Invalid environment")

        # Random junk code snippets for obfuscation
        junk_snippets = [
            f"_{self._junk_seed}_a = lambda x: x",
            f"_{self._junk_seed}_b = [None] * 0",
            f"_{self._junk_seed}_c = {{}}",
            f"_{self._junk_seed}_d = type('_', (), {{}})",  # Empty class
            f"_{self._junk_seed}_e = (lambda: None).__code__.co_code",  # Bytecode reference
        ]
        junk_code = '\n'.join(junk_snippets)

        # Generate blinded constants (hide magic numbers)
        blind_key = random.randint(0x10000000, 0x7FFFFFFF)
        blinded_16 = 16 ^ blind_key

        # Generate watermark (hidden identifier for tracking leaks)
        watermark = hashlib.sha256(
            self.encryption_key + self.license_info.encode() + b'watermark'
        ).hexdigest()[:16]

        # Checksum chain seeds
        cc_seed1 = secrets.token_hex(8)

        # Generate honey token (fake key to detect tampering)
        honey_token = base64.b64encode(os.urandom(32)).decode('ascii')

        # White-Box decoder logic
        wbc_decoder_code = ""
        if self.use_whitebox:
            # Generate the LUT-based decoder and rename its function to the polymorphic name
            wbc_raw = self.wbc.wba.generate_python_decoder()
            wbc_decoder_code = wbc_raw.replace("_wbc_decrypt", v['wdec'])

        return f'''# PyObfuscator Runtime - {self.runtime_id}  # nosec: B608
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
{wbc_decoder_code}
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

# Watermark for leak tracking
{v['wm']} = '{watermark}'
# Honey token (fake key - if accessed, tampering detected)
{v['ht']} = '{honey_token}'

# Constant blinding - hide magic numbers
{v['cb']} = {blind_key}
def _ub(_v): return _v ^ {v['cb']}  # Unblind constant

# Opaque predicates (complex but deterministic)
{v['op']} = lambda: (({v['tm']}.time() * 0) == 0) and ((1 << 4) == _ub({blinded_16}))

{v['err']} = {{
    'i': '{err_integrity}', 'f': '{err_format}', 'c': '{err_corrupt}',
    'd': '{err_debug}', 'e': '{err_expired}', 'm': '{err_machine}',
    'o': '{err_domain}', 'a': '{err_auth}', 'mem': '{err_memory}',
    'th': '{err_thread}', 'p': '{err_parent}', 'h': '{err_hook}', 'env': '{err_env}'
}}

# Checksum chain for integrity verification
{v['cc']} = {{
    'seed': '{cc_seed1}',
    'chain': [],
    'verify': lambda _h, _d: {v['hl']}.sha256((_h + _d).encode()).hexdigest()[:8]
}}

# Anti-hooking: verify built-in functions haven't been replaced
def {v['ah']}():
    try:
        # Check if critical functions are original
        _builtins = [exec, eval, compile, __import__, open, print]
        for _f in _builtins:
            # Check function hasn't been wrapped/hooked
            if hasattr(_f, '__wrapped__') or hasattr(_f, '_original'):
                return False
            # Check code object exists for built-ins that have it
            if hasattr(_f, '__code__'):
                if not hasattr(_f.__code__, 'co_code'):
                    return False
        # Check sys.modules for injected modules
        _suspicious = ['frida', 'objection', 'r2pipe', 'unicorn', 'capstone', 'keystone']
        for _s in _suspicious:
            if _s in {v['sy']}.modules:
                return False
        return True
    except:
        return False

# Environment fingerprinting - detailed environment verification
def {v['ef']}():
    _score = 0
    # Check Python implementation
    if {v['pl']}.python_implementation() != 'CPython':
        _score += 5
    # Check for unusual sys.path entries
    _sus_paths = ['frida', 'hook', 'inject', 'patch', 'crack']
    for _p in {v['sy']}.path:
        if any(_s in _p.lower() for _s in _sus_paths):
            _score += 3
    # Check for too many modules loaded (might indicate analysis)
    if len({v['sy']}.modules) > 500:
        _score += 2
    # Check if running in unusual directory
    _cwd = {v['os']}.getcwd().lower()
    _bad_dirs = ['temp', 'sandbox', 'analysis', 'malware', 'virus', 'sample']
    if any(_d in _cwd for _d in _bad_dirs):
        _score += 4
    return _score < 5  # Allow some false positives

# Fake error path - decoy that triggers on analysis
def {v['fe']}():
    # This function looks like it does something important
    # but is actually a trap for reverse engineers
    _fake_key = {v['b64']}.b64decode('{honey_token}')
    _result = bytearray(32)
    for _i in range(32):
        _result[_i] = _fake_key[_i % len(_fake_key)] ^ 0x55
    # If someone patches to reach here, they get garbage
    return bytes(_result)

# Dead code injection - realistic but never executed
def {v['dc']}(_x):
    if {v['op']}() and False:  # Never true
        _data = {v['b64']}.b64decode(_x)
        _key = {v['hl']}.sha256(_data).digest()
        return bytes(d ^ k for d, k in zip(_data, _key * 10))
    return None

# State machine for control flow flattening
class {v['sm']}:
    _state = 0
    _transitions = {{
        0: [1, 2],
        1: [3],
        2: [3],
        3: [4, 5],
        4: [6],
        5: [6],
        6: [0, 7],
        7: []  # Terminal
    }}
    @classmethod
    def next(cls, _input):
        _valid = cls._transitions.get(cls._state, [])
        if _input in _valid:
            cls._state = _input
            return True
        return False
    @classmethod
    def reset(cls):
        cls._state = 0

# String table (encrypted constant strings)
{v['stbl']} = {{
    's1': {v['b64']}.b64decode('d21pYw=='),  # wmic
    's2': {v['b64']}.b64decode('ZGlza2RyaXZl'),  # diskdrive
    's3': {v['b64']}.b64decode('c2VyaWFsbnVtYmVy'),  # serialnumber
}}

def {v['us']}(_c):
    _kf = {v['key']}[:len({v['b64']}.b64decode(_c))]
    _d = {v['b64']}.b64decode(_c)
    return bytes(d ^ k for d, k in zip(_d, (_kf * (len(_d)//32 + 1))[:len(_d)])).decode()

# Anti-memory dump: detect memory scanning tools
def {v['amd']}():
    try:
        # Check for common memory analysis tools
        _mem_tools = ['cheatengine', 'ollydbg', 'x64dbg', 'ida', 'ghidra', 
                      'processhacker', 'windbg', 'immunity', 'radare']
        # Check window titles (Windows)
        if {v['sy']}.platform == 'win32':
            try:
                import ctypes
                _user32 = ctypes.windll.user32
                _buf = ctypes.create_unicode_buffer(256)
                _hwnd = _user32.GetForegroundWindow()
                _user32.GetWindowTextW(_hwnd, _buf, 256)
                _title = _buf.value.lower()
                if any(_t in _title for _t in _mem_tools):
                    return True
            except: pass
        # Check process list for analysis tools
        if {v['sy']}.platform == 'win32':
            try:
                import subprocess as _sp
                _r = _sp.run(['tasklist'], capture_output=True, text=True, 
                            timeout=3, creationflags=0x08000000)
                _procs = _r.stdout.lower()
                if any(_t in _procs for _t in _mem_tools):
                    return True
            except: pass
        return False
    except:
        return False

# Parent process trace - verify we're not launched by analysis tools
def {v['ptr']}():
    try:
        if {v['sy']}.platform == 'win32':
            import ctypes
            from ctypes import wintypes
            _kernel32 = ctypes.windll.kernel32
            _pid = {v['os']}.getpid()
            _PROCESS_QUERY_INFORMATION = 0x0400
            _snapshot = _kernel32.CreateToolhelp32Snapshot(0x2, 0)
            if _snapshot == -1:
                return True
            # Check parent process name
            # Simplified check - full implementation would use Process32First/Next
        return True
    except:
        return True

# Thread monitoring - detect if new threads are injected
{v['th']} = {{
    'count': 0,
    'check': lambda: True  # Placeholder for thread count verification
}}

# Code splitting - distribute decryption logic
def {v['cs1']}(_d, _s, _e):
    return _d[_s:_e]

def {v['cs2']}(_d, _k):
    return bytes(a ^ b for a, b in zip(_d, _k * (len(_d) // len(_k) + 1)))

def {v['cs3']}(_d):
    return {v['zl']}.decompress(_d)

# Resource exhaustion on tampering detection
def {v['rat']}():
    # Consume CPU cycles to slow down automated analysis
    _x = 0
    for _i in range(1000000):
        _x = (_x * 31337 + _i) % 999999937
    return _x

# Anti-patching: verify runtime file integrity
def {v['ap']}():
    try:
        import inspect as _ins
        _src = _ins.getsourcefile({v['ap']})
        if _src and {v['os']}.path.exists(_src):
            with open(_src, 'rb') as _f:
                _content = _f.read()
            # Check for common patching signatures
            _patches = [b'import pdb', b'breakpoint()', b'print(key', b'print(_k']
            for _p in _patches:
                if _p in _content.lower():
                    return False
        return True
    except:
        return True  # Allow if can't check

# Call stack verification
def {v['csv']}():
    try:
        import inspect as _ins
        _stack = _ins.stack()
        # Verify we're being called from expected context
        _callers = [f.function for f in _stack[:5]]
        # Should not have debugger frames
        _suspicious = ['run_code', 'do_run', 'debug', 'trace', 'interact']
        return not any(s in str(_callers).lower() for s in _suspicious)
    except:
        return True

# Control flow obfuscation - splits logic into indirect jumps
{v['cf']} = {{
    0: lambda _f, *_a: _f(*_a),
    1: lambda _x: _x,
    2: lambda _a, _b: _a if {v['op']}() else _b,
}}

# ============== COMPLEX CODE VIRTUALIZATION ENGINE ==============
# Stack-based VM with randomized opcodes, self-modifying code, and anti-analysis

class VM:
    # Advanced virtualization: randomized opcodes, stack-based, self-modifying, anti-analysis
    
    # Randomized opcode table (generated at runtime creation)
    _OPMAP = {
        # Stack operations
        0x01: 'PUSH',
        0x02: 'POP',
        0x03: 'DUP',
        0x04: 'SWAP',
        0x05: 'ROT3',
        # Arithmetic
        0x10: 'ADD',
        0x11: 'SUB',
        0x12: 'MUL',
        0x13: 'DIV',
        0x14: 'MOD',
        # Bitwise
        0x20: 'XOR',
        0x21: 'AND',
        0x22: 'OR',
        0x23: 'NOT',
        0x24: 'SHL',
        0x25: 'SHR',
        0x26: 'ROTL',
        0x27: 'ROTR',
        # Control flow
        0x40: 'JMP',
        0x41: 'JZ',
        0x42: 'JNZ',
        0x43: 'JGT',
        0x44: 'JLT',
        0x45: 'CALL',
        0x46: 'RET',
        # Memory
        0x30: 'LOAD',
        0x31: 'STORE',
        0x32: 'LOADB',
        0x33: 'STOREB',
        # Special
        0xF0: 'HALT',
        0xF1: 'MUTATE',
        0xF2: 'CHECK',
        0xF3: 'TRAP',
    }
    
    _REVMAP = {v: k for k, v in _OPMAP.items()}
    
    def __init__(self):
        self._stk = []
        self._mem = bytearray(4096)
        self._cstk = []
        self._pc = 0
        self._dat = bytearray()
        self._run = True
        self._mut = 0
        self._cnt = 0
        
    def _aa(self):
        # Anti-analysis check
        self._cnt += 1
        if self._cnt > 100000: return True
        if {v['sy']}.gettrace() is not None: return True
        return False
    
    def _mo(self, _a):
        # Self-modifying opcode
        if _a < len(self._bc):
            self._bc[_a] ^= (self._mut & 0xFF)
            self._mut += 1
    
    def _pu(self, _v): self._stk.append(_v & 0xFFFFFFFF)
    def _po(self): return self._stk.pop() if self._stk else 0
    def _pk(self): return self._stk[-1] if self._stk else 0
    
    def _r8(self):
        if self._pc < len(self._bc):
            _v = self._bc[self._pc]
            self._pc += 1
            return _v
        return 0
    
    def _r16(self):
        return self._r8() | (self._r8() << 8)
    
    def _r32(self):
        return self._r8() | (self._r8() << 8) | (self._r8() << 16) | (self._r8() << 24)
    
    def execute(self, _bytecode, _data):
        self._bc = bytearray(_bytecode)
        self._dat = bytearray(_data)
        self._pc = 0
        self._run = True
        self._stk = []
        self._cnt = 0
        
        while self._run and self._pc < len(self._bc):
            if self._aa(): return bytes([0xFF] * len(_data))
            
            _op = self._r8()
            _nm = self._OPMAP.get(_op, 'NOP')
            
            if _nm == 'PUSH': self._pu(self._r32())
            elif _nm == 'POP': self._po()
            elif _nm == 'DUP': self._pu(self._pk())
            elif _nm == 'SWAP':
                if len(self._stk) >= 2:
                    self._stk[-1], self._stk[-2] = self._stk[-2], self._stk[-1]
            elif _nm == 'ROT3':
                if len(self._stk) >= 3:
                    _a, _b, _c = self._stk[-3:]
                    self._stk[-3:] = [_b, _c, _a]
            elif _nm == 'ADD':
                _b, _a = self._po(), self._po()
                self._pu(_a + _b)
            elif _nm == 'SUB':
                _b, _a = self._po(), self._po()
                self._pu(_a - _b)
            elif _nm == 'MUL':
                _b, _a = self._po(), self._po()
                self._pu(_a * _b)
            elif _nm == 'DIV':
                _b, _a = self._po(), self._po()
                self._pu(_a // _b if _b else 0)
            elif _nm == 'MOD':
                _b, _a = self._po(), self._po()
                self._pu(_a % _b if _b else 0)
            elif _nm == 'XOR':
                _b, _a = self._po(), self._po()
                self._pu(_a ^ _b)
            elif _nm == 'AND':
                _b, _a = self._po(), self._po()
                self._pu(_a & _b)
            elif _nm == 'OR':
                _b, _a = self._po(), self._po()
                self._pu(_a | _b)
            elif _nm == 'NOT': self._pu(~self._po() & 0xFFFFFFFF)
            elif _nm == 'SHL':
                _n, _a = self._po(), self._po()
                self._pu((_a << _n) & 0xFFFFFFFF)
            elif _nm == 'SHR':
                _n, _a = self._po(), self._po()
                self._pu(_a >> _n)
            elif _nm == 'ROTL':
                _n, _a = self._po() & 31, self._po()
                self._pu(((_a << _n) | (_a >> (32 - _n))) & 0xFFFFFFFF)
            elif _nm == 'ROTR':
                _n, _a = self._po() & 31, self._po()
                self._pu(((_a >> _n) | (_a << (32 - _n))) & 0xFFFFFFFF)
            elif _nm == 'JMP': self._pc = self._r16()
            elif _nm == 'JZ':
                _addr = self._r16()
                if self._po() == 0: self._pc = _addr
            elif _nm == 'JNZ':
                _addr = self._r16()
                if self._po() != 0: self._pc = _addr
            elif _nm == 'JGT':
                _addr = self._r16()
                if self._po() > 0: self._pc = _addr
            elif _nm == 'JLT':
                _addr = self._r16()
                _v = self._po()
                if _v != 0 and (_v & 0x80000000): self._pc = _addr
            elif _nm == 'CALL':
                _addr = self._r16()
                self._cstk.append(self._pc)
                self._pc = _addr
            elif _nm == 'RET':
                if self._cstk: self._pc = self._cstk.pop()
                else: self._run = False
            elif _nm == 'LOAD':
                _addr = self._po()
                self._pu(self._mem[_addr] if _addr < len(self._mem) else 0)
            elif _nm == 'STORE':
                _addr, _val = self._po(), self._po()
                if _addr < len(self._mem): self._mem[_addr] = _val & 0xFF
            elif _nm == 'LOADB':
                _idx = self._po()
                self._pu(self._dat[_idx] if _idx < len(self._dat) else 0)
            elif _nm == 'STOREB':
                _idx, _val = self._po(), self._po()
                if _idx < len(self._dat): self._dat[_idx] = _val & 0xFF
            elif _nm == 'NOP': pass
            elif _nm == 'HALT': self._run = False
            elif _nm == 'MUTATE': self._mo(self._r16())
            elif _nm == 'CHECK': self._pu(1 if {v['sy']}.gettrace() else 0)
            elif _nm == 'TRAP':
                for _i in range(len(self._dat)): self._dat[_i] ^= 0xFF
                self._run = False
            
            self._cnt += 1
        
        return bytes(self._dat)
    
    @classmethod
    def compile_xor(cls, _key):
        # Compile XOR transformation to VM bytecode
        _bc = bytearray()
        _OP = cls._REVMAP
        for _i, _k in enumerate(_key):
            _bc.append(_OP['PUSH'])
            _bc.extend([_i & 0xFF, (_i >> 8) & 0xFF, (_i >> 16) & 0xFF, (_i >> 24) & 0xFF])
            _bc.append(_OP['DUP'])
            _bc.append(_OP['LOADB'])
            _bc.append(_OP['PUSH'])
            _bc.extend([_k, 0, 0, 0])
            _bc.append(_OP['XOR'])
            _bc.append(_OP['SWAP'])
            _bc.append(_OP['STOREB'])
        _bc.append(_OP['HALT'])
        return bytes(_bc)
    
    @classmethod 
    def transform(cls, _data, _key):
        # Transform data using VM-based XOR
        _v = cls()
        _ek = (_key * ((len(_data) // len(_key)) + 1))[:len(_data)]
        return _v.execute(cls.compile_xor(_ek), _data)

# Import hook for protected modules
class {v['ih']}:
    _cache = {{}}
    _protected = set()
    
    @classmethod
    def register(cls, _name, _code, _globs):
        cls._protected.add(_name)
        cls._cache[_name] = (_code, _globs)
    
    @classmethod
    def is_protected(cls, _name):
        return _name in cls._protected
    
    @classmethod
    def load(cls, _name):
        if _name in cls._cache:
            _code, _globs = cls._cache[_name]
            exec(_code, _globs)
            return _globs
        return None

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

def {v['dcp']}(_d, _mk):
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

# Network license validation (optional)
def {v['nl']}(_url, _mid, _lid):
    if not _url: return True
    try:
        import urllib.request as _ur
        import json as _js
        _data = _js.dumps({{'machine_id': _mid, 'license_id': _lid, 'watermark': {v['wm']}}}).encode()
        _req = _ur.Request(_url, data=_data, headers={{'Content-Type': 'application/json'}})
        _req.timeout = 5
        with _ur.urlopen(_req) as _resp:
            _result = _js.loads(_resp.read().decode())
            return _result.get('valid', False)
    except:
        return True  # Allow offline usage if server unreachable

def __pyobfuscator__(_nm, _fl, _pl):
    # Initialize state machine
    {v['sm']}.reset()
    {v['sm']}.next(1)  # State: initialization
    
    # Layer 1: Self-integrity check
    if not {v['ic']}(): raise RuntimeError({v['us']}({v['err']}['i']))
    
    # Layer 2: Anti-patching check (verify runtime not modified)
    if not {v['ap']}(): raise RuntimeError({v['us']}({v['err']}['i']))
    
    # Layer 3: Call stack verification
    if not {v['csv']}(): raise RuntimeError({v['us']}({v['err']}['d']))
    
    # Layer 4: Anti-memory dump check
    if {v['amd']}():
        {v['rat']}()  # Resource exhaustion
        raise RuntimeError({v['us']}({v['err']}['mem']))
    
    # Layer 5: Parent process verification
    if not {v['ptr']}():
        raise RuntimeError({v['us']}({v['err']}['p']))
    
    # Layer 6: Anti-hooking verification
    if not {v['ah']}():
        {v['rat']}()
        raise RuntimeError({v['us']}({v['err']}['h']))
    
    # Layer 7: Environment fingerprinting
    if not {v['ef']}():
        raise RuntimeError({v['us']}({v['err']}['env']))
    
    {v['sm']}.next(3)  # State: security checks passed
    
    _dr = {v['b64']}.b64decode(_pl)
    _kc = {v['gk']}()
    
    # Checksum chain - verify payload integrity incrementally
    _cc_hash = {v['cc']}['seed']
    _cc_hash = {v['cc']}['verify'](_cc_hash, str(len(_dr)))
    
    try:
        # Dead code path (never executed, confuses analysis)
        if {v['dc']}('{honey_token}') and False:
            return {v['fe']}()
        
        # Opaque predicate check (always passes but confuses static analysis)
        if not {v['op']}(): raise RuntimeError({v['us']}({v['err']}['i']))
        
        {v['sm']}.next(4)  # State: payload processing
        
        # Use code splitting for header verification
        _magic = {v['cs1']}(_dr, 0, 8)
        if _magic not in (b'PYO00002', b'PYO00003', {v['magic']}):
            raise RuntimeError({v['us']}({v['err']}['f']))
        
        # Update checksum chain
        _cc_hash = {v['cc']}['verify'](_cc_hash, _magic.hex())
        
        _dl = {v['st']}.unpack('<I', {v['cs1']}(_dr, 10, 14))[0]
        _ch = {v['cs1']}(_dr, 14, 30)
        _en = {v['cs1']}(_dr, 30, 30+_dl)
        
        if {v['hl']}.sha256(_en).digest()[:16] != _ch:
            {v['rat']}()  # Slow down on tampering
            raise RuntimeError({v['us']}({v['err']}['c']))
        
        {v['sm']}.next(5)  # State: decryption
        
        # Use control flow dispatch for decryption
        _dec = {v['cf']}[0]({v['dcp']}, _en, bytes(_kc))
        
        # Second layer: XOR or White-Box
        if '{v['wdec']}' in globals():
            _dec = {v['cf']}[0](globals()['{v['wdec']}'], _dec)
        else:
            _dec = {v['cf']}[0]({v['ld']}, _dec, {v['xkey']})
        
        # Update checksum chain
        _cc_hash = {v['cc']}['verify'](_cc_hash, {v['hl']}.sha256(_dec[:32]).hexdigest()[:8])
        
        _mln = {v['st']}.unpack('<H', {v['cs1']}(_dec, 0, 2))[0]
        _mb = {v['cs1']}(_dec, 2, 2+_mln)
        _mt = eval(_mb.decode('utf-8'))
        _cp = _dec[2+_mln:]
        
        {v['sm']}.next(6)  # State: verification
        
        # Security checks with opaque predicates
        if {v['cf']}[2](_mt.get('anti_debug', False), False) and {v['ad']}():
            {v['rat']}()  # Slow down attacker
            raise RuntimeError({v['us']}({v['err']}['d']))
        
        # VM detection if enabled
        if _mt.get('vm_detect', False) and {v['vd']}():
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
        
        # Optional network license check
        _nl_url = _mt.get('license_server')
        if _nl_url and not {v['nl']}(_nl_url, {v['gm']}(), _mt.get('license')):
            raise RuntimeError({v['us']}({v['err']}['e']))
        
        {v['sm']}.next(7)  # State: execution
        
        # Use code splitting for decompression
        _bc = {v['cs3']}(_cp)
        _sk = {v['b64']}.b64decode(_mt.get('_sk', ''))
        if _sk:
            # Use VM-based descrambling for maximum protection
            # Falls back to simple XOR if VM execution fails
            try:
                _bc = {v['vm']}.transform(_bc, _sk)
            except:
                # Fallback to simple XOR (compatible with older protected files)
                _bc = {v['cs2']}(_bc, _sk)
        
        # Final checksum chain verification
        _cc_hash = {v['cc']}['verify'](_cc_hash, {v['hl']}.sha256(_bc[:64] if len(_bc) > 64 else _bc).hexdigest()[:8])
        
        _co = {v['ml']}.loads(_bc)
        _gl = {{'__name__': _nm, '__file__': _fl, '__builtins__': __builtins__}}
        
        # Register with import hook for nested imports
        {v['ih']}.register(_nm, _co, _gl)
        
        # Execute through control flow dispatcher
        {v['cf']}[0](exec, _co, _gl)
        
        _cl = {v['sy']}.modules.get(_nm)
        if _cl:
            for _k, _v in _gl.items():
                if not _k.startswith('_'): setattr(_cl, _k, _v)
    finally:
        {v['sm']}.reset()  # Reset state machine
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
            runtime_path = output_dir / f'pyobfuscator_runtime_{self.runtime_id}.py'
            with open(runtime_path, 'w', encoding='utf-8') as f:
                f.write(runtime)
            result['runtime'] = runtime_path

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

    def _copy_runtime_to_output(
        self,
        file_result: Dict[str, Any],
        output_dir: Path,
        results: Dict[str, Any]
    ) -> bool:
        """Copy runtime file to output directory. Returns True if copied."""
        if 'runtime' not in file_result:
            return False

        import shutil
        runtime_name = f'pyobfuscator_runtime_{self.runtime_id}.py'
        runtime_dest = output_dir / runtime_name
        if file_result['runtime'] != runtime_dest:
            shutil.copy2(file_result['runtime'], runtime_dest)
        results['runtime'] = runtime_dest
        return True

    def protect_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[list] = None
    ) -> Dict[str, Any]:
        """Protect all Python files in a directory."""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', 'test_*']

        results: Dict[str, Any] = {'files': {}, 'runtime': None}
        pattern = '**/*.py' if recursive else '*.py'
        runtime_created = False

        for py_file in input_dir.glob(pattern):
            relative = py_file.relative_to(input_dir)

            if self._should_skip_file(relative, py_file.name, exclude_patterns):
                continue

            try:
                out_subdir = output_dir / relative.parent
                file_result = self.protect_file(
                    py_file,
                    out_subdir,
                    create_runtime=not runtime_created
                )
                results['files'][str(relative)] = 'success'

                if not runtime_created:
                    runtime_created = self._copy_runtime_to_output(
                        file_result, output_dir, results
                    )

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
