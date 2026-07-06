import base64
import json
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


TGS_SECRET_KEY = "IRpMmtvhXXphfL6MzrRMOOK1EB8jlwN82/Fza1I5j7I="

SERVICE_KEYS = {
    "service1": "fAJHyqCDIsyyi+eTMVqgFjl7yM5ijOvcqXYJ7RlhHXs="
}

def generate_key():
    return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")


def derive_kerberos_key(password, user):
    salt_string = f"unb.br{user}"
    static_salt = salt_string.encode("utf-8")
    password_bytes = password.encode("utf-8")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=static_salt,
        iterations=1000,
    )

    return base64.b64encode(kdf.derive(password_bytes)).decode("utf-8")


def _decode_key(key_base64):
    return base64.b64decode(key_base64.encode("utf-8"))


def encrypt_json(key_base64, payload):

    key = _decode_key(key_base64)
    aesgcm = AESGCM(key)

    nonce = secrets.token_bytes(12)
    plaintext = json.dumps(payload).encode("utf-8")

    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    return {
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8")
    }


def decrypt_json(key_base64, encrypted_payload):

    key = _decode_key(key_base64)
    aesgcm = AESGCM(key)

    nonce = base64.b64decode(encrypted_payload["nonce"])
    ciphertext = base64.b64decode(encrypted_payload["ciphertext"])

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return json.loads(plaintext.decode("utf-8"))