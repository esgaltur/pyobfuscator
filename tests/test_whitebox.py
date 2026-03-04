# -*- coding: utf-8 -*-
import unittest
from pyobfuscator.crypto.whitebox import WhiteBoxEngine

class TestWhiteBox(unittest.TestCase):
    def test_roundtrip(self):
        key = b"this-is-a-32-byte-secret-key-123"
        engine = WhiteBoxEngine(key)
        
        secret = b"Principal Engineer Secret Data"
        encrypted = engine.encrypt(secret)
        
        # Test the generated Python decoder
        decoder_code = engine.wba.generate_python_decoder()
        namespace = {}
        exec(decoder_code, namespace)
        
        decrypted_padded = namespace['_wbc_decrypt'](encrypted)
        
        # Remove PKCS#7-like padding
        pad_len = decrypted_padded[-1]
        decrypted = decrypted_padded[:-pad_len]
        
        self.assertEqual(secret, decrypted)
        self.assertNotEqual(secret, encrypted)

if __name__ == "__main__":
    unittest.main()
