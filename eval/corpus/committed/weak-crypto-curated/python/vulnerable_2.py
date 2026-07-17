"""Weak cipher: DES used for encryption (CWE-327)."""

from Crypto.Cipher import DES


def make_cipher(key: bytes) -> object:
    return DES.new(key, DES.MODE_ECB)  # sast:vuln
