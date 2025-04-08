import secrets
import os
from typing import Dict
from utils import setup_logger


class CryptoManager:
    """
    Handles all cryptographic operations for the system
    """
    def __init__(self, master_key_path: str):
        self.master_key_path = master_key_path
        self.master_key = self._load_or_create_master_key()
        self.file_keys: Dict[str, bytes] = {} # file_id -> key mapping
        self.logger = setup_logger(logger_name='crypto_manager', log_file='logs/crypto_manager.log')
    
    def _load_or_create_master_key(self) -> bytes:
        """
        Load the master key or create one if it doesn't exist
        
        Returns:
            bytes: A 32-byte (256-bit) master key.
            
        Raises:
            OSError: If file operations fail
            ValueError: If the key file exists but is corrupted
        """
        # Use absolute path and normalize for security
        key_path = os.path.abspath(os.path.normpath(self.master_key_path))
        try:
            # Attempt to read existing key with exclusive access
            with open(key_path, 'rb') as f:
                key = f.read()
                
            # Validate key integrity
            if not key or len(key) != 32:
                self.logger.error("Master key file is invalid or corrupted")
                raise ValueError("Master key has invalid length or is empty")
            
            return key
            
        except FileNotFoundError:
            self.logger.warning("Master key file not found. Generating a new one")
            
            # Generate cryptographically secure key
            key = secrets.token_bytes(32)
            
            # Ensure parent directory exists with secure permissions
            key_dir = os.path.dirname(self.master_key_path)
            try:
                # Create directory with secure permissions if it doesn't exist
                if not os.path.exists(key_dir):
                    os.makedirs(key_dir, mode=0o600, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Could not create key directory: {e}")
                raise
            
            # Create a temporary file in the same directory for atomic move
            temp_path = f"{key_path}.{os.getpid()}.tmp"
            try:
                # Create with secure permissions from the start
                fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    with os.fdopen(fd, 'wb') as f:
                        f.write(key)
                except Exception as e:
                    # Make sure we don't leave fd open if write fails
                    os.close(fd)
                    raise
                
                # Atomic rename for crash safety
                os.rename(temp_path, key_path)
                
                self.logger.info("Successfully created new master key")
                return key
            
            except OSError as e:
                self.logger.error(f"Cound not create master key file: {e}")
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise