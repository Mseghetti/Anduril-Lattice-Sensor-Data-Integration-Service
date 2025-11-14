"""Lattice REST API client implementation."""

import os
import time
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logging import get_logger

logger = get_logger(__name__)


class LatticeClient:
    """REST API client for Anduril Lattice."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        environment: str = "production",
        timeout: float = 10.0,
    ):
        """
        Initialize Lattice REST API client.
        
        Args:
            api_key: Lattice API key (or from LATTICE_API_KEY env var)
            api_url: Lattice API base URL (or from LATTICE_API_URL env var)
            environment: Environment name (production, staging, etc.)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("LATTICE_API_KEY")
        self.api_url = (api_url or os.getenv("LATTICE_API_URL", "https://api.anduril.com")).rstrip("/")
        self.environment = environment
        self.timeout = timeout
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            self._mock_mode = False
            logger.info(f"Lattice REST client initialized for {self.environment}")
        else:
            self._mock_mode = True
            logger.warning("No API key provided. Running in mock mode.")
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to Lattice.
        
        Returns:
            True if connected, False otherwise
        """
        return not self._mock_mode
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[requests.Response]:
        """
        Make HTTP request to Lattice API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            data: Optional request body data
            params: Optional query parameters
            
        Returns:
            Response object or None if failed
        """
        if self._mock_mode:
            logger.debug(f"Mock {method} request to {endpoint}")
            return None
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {endpoint} - {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
    
    def publish_entity(self, entity_data: Dict) -> bool:
        """
        Publish an entity update to Lattice using PUT/PATCH.
        
        Args:
            entity_data: Entity data dictionary formatted for Lattice API
            
        Returns:
            True if successful, False otherwise
        """
        if self._mock_mode:
            logger.debug(f"Mock publish entity: {entity_data.get('id', 'unknown')}")
            return True
        
        entity_id = entity_data.get("id")
        if not entity_id:
            logger.error("Entity data missing 'id' field")
            return False
        
        # Use PUT to create/update entity
        # Endpoint: PUT /api/v1/entities/{entity_id}
        endpoint = f"/api/v1/entities/{entity_id}"
        
        response = self._make_request("PUT", endpoint, data=entity_data)
        
        if response:
            logger.debug(f"Published entity: {entity_id}")
            return True
        
        return False
    
    def publish_entities_batch(self, entities: List[Dict]) -> Dict[str, bool]:
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
        
        # Try batch endpoint first: POST /api/v1/entities/batch
        endpoint = "/api/v1/entities/batch"
        response = self._make_request("POST", endpoint, data={"entities": entities})
        
        if response:
            try:
                response_data = response.json()
                # If batch endpoint returns individual results
                if isinstance(response_data, dict) and "results" in response_data:
                    for result in response_data["results"]:
                        entity_id = result.get("id", "unknown")
                        results[entity_id] = result.get("success", False)
                else:
                    # Assume all succeeded if batch endpoint accepted
                    for entity in entities:
                        entity_id = entity.get("id", "unknown")
                        results[entity_id] = True
                logger.debug(f"Published batch of {len(entities)} entities")
            except Exception as e:
                logger.error(f"Error parsing batch response: {e}")
                # Fall back to individual publishes
                for entity in entities:
                    entity_id = entity.get("id", "unknown")
                    results[entity_id] = False
        else:
            # Fall back to individual publishes if batch fails
            logger.warning("Batch endpoint failed, falling back to individual publishes")
            for entity in entities:
                entity_id = entity.get("id", "unknown")
                results[entity_id] = self.publish_entity(entity)
        
        return results
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity data dictionary or None if not found
        """
        if self._mock_mode:
            logger.debug(f"Mock get entity: {entity_id}")
            return None
        
        endpoint = f"/api/v1/entities/{entity_id}"
        response = self._make_request("GET", endpoint)
        
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Error parsing entity response: {e}")
        
        return None
    
    def list_entities(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        List entities with optional filtering.
        
        Args:
            entity_type: Optional entity type filter
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of entity dictionaries
        """
        if self._mock_mode:
            logger.debug("Mock list entities")
            return []
        
        endpoint = "/api/v1/entities"
        params = {"limit": limit, "offset": offset}
        if entity_type:
            params["type"] = entity_type
        
        response = self._make_request("GET", endpoint, params=params)
        
        if response:
            try:
                data = response.json()
                if isinstance(data, dict) and "entities" in data:
                    return data["entities"]
                elif isinstance(data, list):
                    return data
            except Exception as e:
                logger.error(f"Error parsing entities list: {e}")
        
        return []
    
    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if successful, False otherwise
        """
        if self._mock_mode:
            logger.debug(f"Mock delete entity: {entity_id}")
            return True
        
        endpoint = f"/api/v1/entities/{entity_id}"
        response = self._make_request("DELETE", endpoint)
        
        return response is not None
    
    def get_health(self) -> Dict:
        """
        Get client health status.
        
        Returns:
            Dictionary with health information
        """
        health = {
            "connected": self.is_connected(),
            "mock_mode": self._mock_mode,
            "environment": self.environment,
            "api_url": self.api_url if not self._mock_mode else None,
        }
        
        # Try to ping the API if connected
        if not self._mock_mode:
            try:
                # Try a simple GET to health/status endpoint
                response = self._make_request("GET", "/api/v1/health")
                health["api_accessible"] = response is not None
            except Exception:
                health["api_accessible"] = False
        
        return health
