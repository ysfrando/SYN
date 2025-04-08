import json
import os
import asyncio
from typing import Dict, Any
from utils import setup_logger, load_config
from storage import FileManager
from crypto import CryptoManager
from node import NodeManager

class SecureStorage:
    """
    Main orchestrator for the secure distributed storage system
    """
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = setup_logger(logger_name='secure_storage', log_file='logs/secure_storage.log')
        self.crypto_manager = CryptoManager(self.config['master_key_path'])
        self.node_manager = NodeManager(
            self.config["nodes_db_path"],
            self.crypto_manager,
            use_tor=self.config["use_tor"]
        )
        self.file_manager = FileManager(
            self.config["local_storage_path"],
            self.crypto_manager,
            self.node_manager
        )
        self.running = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                config = json.loads(f)
                
            # Validate required fields
            required_fields = [
                "master_key_path", "nodes_db_path",
                "local_storage_path", "replication_factor",
                "use_tor"
            ]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
                
            return config
        except FileNotFoundError:
            # Create default config
            default_config = {
                "master_key_path": "master.key",
                "nodes_db_path": "nodes.db",
                "local_storage_path": "local_storage",
                "replication_factor": 3,
                "use_tor": True,
                "chunk_size": 4 * 1024 * 1024
            }
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config
    
    async def start(self):
        """Start the storage system"""
        self.logger.info("Starting Secure Storage System")
        self.running = True
        
        # Initialize components
        await self.node_manager.initialize()
        await self.file_manager.initialize()
        
        # Start background tasks
        asyncio.create_task(self._periodic_health_check())
        asyncio.create_task(self._periodic_rebalance())
        
        self.logger.info("System started successfully")
        
    async def stop(self):
        """Stop the storage system"""
        self.logger.info("Stopping Secure Storage System") 
        self.running = False
        
        # Clean up resources
        await self.node_manager.shutdown()
        await self.file_manager.shutdown()
        
        self.logger.info("System stopped successfully")    
        
    async def _periodic_health_check(self):
        """Periodically check the health of storage nodes"""
        while self.running:
            try:
                self.logger.debug("Running periodic health check")   
                await self.node_manager.check_nodes_health()
            except Exception as e:
                self.logger.error(f"Error in health check: {e}")
            
            await asyncio.sleep(300) # Run every 5 minutes
            
    async def _periodic_rebalance(self):
        """Periodically rebalance data across nodes if needed"""
        while self.running:
            try:
                self.logger.debug("Running periodic rebalance")
                await self.file_manager.rebalance_data()
            except Exception as e:
                self.logger.error(f"Error in rebalance: {e}")
                
            await asyncio.sleep(3600) # Run every hour