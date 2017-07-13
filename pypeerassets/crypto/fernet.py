from cryptography.fernet import Fernet as F


class Fernet:

    def __init__(self, message, key):

        if isinstance(key, str):
            key = key.encode()
        if isinstance(message, str):
            message = message.encode()

        self.key = key
        self.cipher = F(self.key)
        self.message = message

    def encrypt(self):
        self.message = self.cipher.encrypt(self.message)
        return self.message

    def decrypt(self):
        self.message = self.cipher.decrypt(self.message)
        return self.message
