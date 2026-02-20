"""
Pollivu - AES-256 Encryption Utility
End-to-end encryption for all sensitive data stored in the database.
Uses AES-256-GCM for authenticated encryption.
"""

import os
import base64
import hashlib
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json

logger = logging.getLogger(__name__)


class AES256Encryption:
    """
    AES-256-GCM encryption for sensitive data.
    
    Features:
    - 256-bit key strength (military-grade encryption)
    - GCM mode for authenticated encryption (tamper-proof)
    - Random nonce for each encryption operation
    - PBKDF2 key derivation from app secret
    """
    
    # AES-256 requires 32-byte (256-bit) key
    KEY_SIZE = 32
    # GCM nonce size (96 bits is recommended)
    NONCE_SIZE = 12
    
    def __init__(self, secret_key: str, salt: bytes = None):
        """
        Initialize encryption with the app's secret key.
        
        Args:
            secret_key: The application's secret key
            salt: Optional salt for key derivation (defaults to env var or app-specific salt)
        """
        # Use provided salt, or env var, or default
        if salt:
            self.salt = salt
        else:
            env_salt = os.environ.get('POLLIVU_SALT')
            if env_salt:
                self.salt = env_salt.encode('utf-8')
            else:
                raise ValueError("POLLIVU_SALT environment variable is required for encryption")
        self._key = self._derive_key(secret_key)
        self._aesgcm = AESGCM(self._key)
    
    def _derive_key(self, secret_key: str) -> bytes:
        """
        Derive a 256-bit key from the secret key using PBKDF2.
        
        Uses PBKDF2 with SHA-256 and 100,000 iterations for secure key derivation.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(secret_key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded string containing nonce + ciphertext
        """
        if not plaintext:
            return ""
        
        # Generate random nonce for this encryption
        nonce = os.urandom(self.NONCE_SIZE)
        
        # Encrypt data
        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # No additional authenticated data
        )
        
        # Combine nonce + ciphertext and base64 encode
        encrypted_data = nonce + ciphertext
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted: Base64-encoded string containing nonce + ciphertext
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails (tampered data)
        """
        if not encrypted:
            return ""
        
        try:
            # Decode base64
            encrypted_data = base64.urlsafe_b64decode(encrypted.encode('utf-8'))
            
            # Extract nonce and ciphertext
            nonce = encrypted_data[:self.NONCE_SIZE]
            ciphertext = encrypted_data[self.NONCE_SIZE:]
            
            # Decrypt and verify
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.warning(f"Decryption failed — possible data tampering: {e}")
            raise ValueError(f"Decryption failed - data may be tampered: {e}")
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON."""
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, encrypted: str) -> dict:
        """Decrypt to a dictionary from JSON."""
        decrypted = self.decrypt(encrypted)
        return json.loads(decrypted) if decrypted else {}
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Create a SHA-256 hash of a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()


# Cache instances by secret key to avoid expensive PBKDF2 re-derivation
# but support multiple keys if needed
_encryption_instances = {}


def get_encryption(secret_key: str) -> AES256Encryption:
    """Get or create the encryption singleton for a specific key."""
    global _encryption_instances
    if secret_key not in _encryption_instances:
        _encryption_instances[secret_key] = AES256Encryption(secret_key)
    return _encryption_instances[secret_key]


def encrypt_data(data: str, secret_key: str) -> str:
    """Convenience function to encrypt data."""
    return get_encryption(secret_key).encrypt(data)


def decrypt_data(encrypted: str, secret_key: str) -> str:
    """Convenience function to decrypt data."""
    return get_encryption(secret_key).decrypt(encrypted)


def encrypt_dict(data: dict, secret_key: str) -> str:
    """Convenience function to encrypt a dictionary."""
    return get_encryption(secret_key).encrypt_dict(data)


def decrypt_dict(encrypted: str, secret_key: str) -> dict:
    """Convenience function to decrypt a dictionary."""
    return get_encryption(secret_key).decrypt_dict(encrypted)
