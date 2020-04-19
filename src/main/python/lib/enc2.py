#!/usr/bin/env python3
# AES 256 encryption/decryption using pycrypto library
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import string
import random
import base64
import hashlib
backend = default_backend()

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

# make 32 byte bytes object
def get_private_key(password):
    salt = b"salty"
    passwd = str.encode(password)
    dk = hashlib.pbkdf2_hmac('sha256', passwd, salt, 100000).hex()
    key = str.encode(dk[:32])
    return key

def encrypt(raw_data, password):
    key = get_private_key(password)

    raw = pad(raw_data).encode("utf8")
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(raw) + encryptor.finalize()
    return base64.b64encode(iv + ct)

def decrypt(enc_data, password):
    key = get_private_key(password)
    enc = base64.b64decode(enc_data)
    iv = enc[:16]   
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)   
    decryptor = cipher.decryptor()
    un_enc = unpad(decryptor.update(enc[16:]) + decryptor.finalize())
    return un_enc

def genPass(stringLength=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(stringLength))

def decrypt_mm2_json(encrypted_mm2_json_data, password):
    mm2_json = decrypt(encrypted_mm2_json_data, password)
    return mm2_json

def encrypt_mm2_json(mm2_json_data, password):    
    mm2_json = encrypt(mm2_json_data, password)
    return mm2_json



