#!/usr/bin/env python3
# AES 256 encryption/decryption using pycrypto library
import string
import random
import base64
from Cryptodome.Cipher import AES
from Cryptodome import Random
from Cryptodome.Protocol.KDF import PBKDF2

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def get_private_key(password):
    salt = b"salty"
    kdf = PBKDF2(password, salt, 64, 1000)
    key = kdf[:32]
    return key

def encrypt(raw, password):
    private_key = get_private_key(password)
    raw = pad(raw).encode("utf8")
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw))

def decrypt(enc, password):
    private_key = get_private_key(password)
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:]))

def genPass(stringLength=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(stringLength))

def decrypt_mm2_json(encrypted_mm2_json_data, password):
    mm2_json = decrypt(encrypted_mm2_json_data, password)
    return mm2_json

def encrypt_mm2_json(mm2_json_data, password):    
    mm2_json = encrypt(mm2_json_data, password)
    return mm2_json