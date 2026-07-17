"""Safe: AES-GCM used for encryption (CWE-327)."""

from Crypto.Cipher import AES


def make_cipher(key: bytes) -> object:
    return AES.new(key, AES.MODE_GCM)  # sast:safe
