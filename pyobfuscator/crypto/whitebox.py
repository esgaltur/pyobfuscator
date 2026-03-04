# -*- coding: utf-8 -*-
"""
White-Box Cryptography Engine for PyObfuscator.

Implements a Look-Up Table (LUT) based symmetric encryption where the key 
is baked into the algorithm's state transitions.
"""

import os
import secrets
import hashlib
from typing import List, Tuple

class WhiteBoxAES:
    """
    Simplified White-Box symmetric engine.
    Instead of a single key, it uses a series of Randomized Affine 
    Transformations and Substitution Tables (S-Boxes).
    """

    def __init__(self, seed_key: bytes):
        # Generate 16 different 256-byte S-Boxes based on the seed key
        self.tables: List[List[int]] = []
        for i in range(16):
            # Derive a unique sub-seed for each table
            sub_seed = hashlib.sha256(seed_key + bytes([i])).digest()
            state = list(range(256))
            
            # Deterministic shuffle using sub_seed as entropy
            # (Fisher-Yates with LCG)
            current_seed = int.from_bytes(sub_seed[:4], 'little')
            for j in range(255, 0, -1):
                current_seed = (current_seed * 1103515245 + 12345) & 0x7FFFFFFF
                target = current_seed % (j + 1)
                state[j], state[target] = state[target], state[j]
            
            self.tables.append(state)

    def transform_block(self, block: bytes) -> bytes:
        """Transforms a 16-byte block using the baked LUTs."""
        if len(block) != 16:
            raise ValueError("Block size must be 16")
        
        output = bytearray(16)
        for i in range(16):
            # The "decryption" is actually a state transition through the LUT
            output[i] = self.tables[i][block[i]]
        return bytes(output)

    def generate_python_decoder(self) -> str:
        """
        Generates a Python string containing the baked LUTs.
        This string contains no contiguous secret key.
        """
        table_data = repr(self.tables)
        return f"""
def _wbc_decrypt(data, tables={table_data}):
    out = bytearray()
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        for j in range(len(chunk)):
            out.append(tables[j % 16][chunk[j]])
    return bytes(out)
"""

class WhiteBoxEngine:
    """
    Principal interface for White-Box operations.
    """
    def __init__(self, key: bytes):
        self.wba = WhiteBoxAES(key)

    def encrypt(self, data: bytes) -> bytes:
        # Padding to 16 bytes
        pad_len = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_len] * pad_len)
        
        # In White-Box, we use the tables in reverse for encryption
        # (or just use the tables as a non-standard cipher)
        # For simplicity in this implementation, we'll treat the tables
        # as the 'Key Space' itself.
        
        # To encrypt, we need the inverse tables
        inv_tables = []
        for t in self.wba.tables:
            inv = [0] * 256
            for idx, val in enumerate(t):
                inv[val] = idx
            inv_tables.append(inv)
            
        output = bytearray()
        for i in range(0, len(padded_data), 16):
            chunk = padded_data[i:i+16]
            for j in range(len(chunk)):
                output.append(inv_tables[j % 16][chunk[j]])
        return bytes(output)
