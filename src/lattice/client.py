"""Lattice SDK client wrapper."""

import os
from typing import Dict, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)

try:
    from anduril_lattice_sdk import LatticeClient as SDKClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("anduril-lattice-sdk not available. Using mock client.")


class LatticeClient:
    """Wrapper for Anduril Lattice SDK client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        environment: str = "production",
    ):
        """
        Initialize Lattice client.
        
        Args:
            api_key: Lattice API key (or from LATTICE_API_KEY env var)
            api_url: Lattice API URL (or from LATTICE_API_URL env var)
            environment: Environment name (production, staging, etc.)
        """
        self.api_key = api_key or os.getenv("LATTICE_API_KEY")
        self.api_url = api_url or os.getenv("LATTICE_API_URL", "https://api.anduril.com")
        self.environment = environment
        
        if SDK_AVAILABLE and self.api_key:
            try:
                self._client = SDKClient(
                    api_key=self.api_key,
                    base_url=self.api_url,
                    environment=self.environment,
                )
                self._mock_mode = False
                logger.info(f"Lattice client initialized for {self.environment}")
            except Exception as e:
                logger.error(f"Failed to initialize Lattice SDK client: {e}")
                self._client = None
                self._mock_mode = True
        else:
            self._client = None
            self._mock_mode = True
            if not self.api_key:
                logger.warning("No API key provided. Running in mock mode.")
            else:
                logger.warning("Lattice SDK not available. Running in mock mode.")
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to Lattice.
        
        Returns:
            True if connected, False otherwise
        """
        return not self._mock_mode and self._client is not None
    
    def publish_entity(self, entity_data: Dict) -> bool:
        """
        Publish an entity update to Lattice.
        
        Args:
            entity_data: Entity data dictionary formatted for Lattice API
            
        Returns:
            True if successful, False otherwise
        """
        if self._mock_mode:
            logger.debug(f"Mock publish: {entity_data.get('id', 'unknown')}")
            return True
        
        try:
            if self._client:
                # Assuming the SDK has an entities.update() method
                # This will need to be adjusted based on actual SDK API
                response = self._client.entities.update(entity_data)
                logger.debug(f"Published entity: {entity_data.get('id', 'unknown')}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to publish entity: {e}")
            return False
    
    def publish_entities_batch(self, entities: list[Dict]) -> Dict[str, bool]:
        """
        Publish multiple entities in a batch.
        
        Args:
            entities: List of entity data dictionaries
            
        Returns:
            Dictionary mapping entity IDs to success status
        """
        results = {}
        
        if self._mock_mode:
            for entity in entities:
                entity_id = entity.get("id", "unknown")
                logger.debug(f"Mock batch publish: {entity_id}")
                results[entity_id] = True
            return results
        
        try:
            if self._client:
                # Assuming the SDK supports batch updates
                # This will need to be adjusted based on actual SDK API
                response = self._client.entities.update_batch(entities)
                for entity in entities:
                    entity_id = entity.get("id", "unknown")
                    results[entity_id] = True
                logger.debug(f"Published batch of {len(entities)} entities")
                return results
        except Exception as e:
            logger.error(f"Failed to publish batch: {e}")
            for entity in entities:
                entity_id = entity.get("id", "unknown")
                results[entity_id] = False
        
        return results
    
    def get_health(self) -> Dict:
        """
        Get client health status.
        
        Returns:
            Dictionary with health information
        """
        return {
            "connected": self.is_connected(),
            "mock_mode": self._mock_mode,
            "environment": self.environment,
            "api_url": self.api_url if not self._mock_mode else None,
        }

