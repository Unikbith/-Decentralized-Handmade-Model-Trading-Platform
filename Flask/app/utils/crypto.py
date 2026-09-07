"""密码加解密工具（Fernet 对称加密，密钥持久化到 secret.key）"""
from cryptography.fernet import Fernet

from ..config import BASE_DIR

SECRET_KEY_FILE = BASE_DIR / 'secret.key'


def _load_cipher():
    if not SECRET_KEY_FILE.exists():
        key = Fernet.generate_key()
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
    with open(SECRET_KEY_FILE, 'rb') as f:
        return Fernet(f.read())


cipher_suite = _load_cipher()


def encrypt_password(password):
    return cipher_suite.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password):
    return cipher_suite.decrypt(encrypted_password.encode()).decode()
