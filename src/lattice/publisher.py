"""Lattice entity publisher with retry logic and error handling."""

import time
from typing import Dict, List, Optional

from ..sensors.base import SensorReading
from ..simulation.entities import Entity
from ..utils.logging import get_logger
from ..utils.metrics import MetricsCollector
from .client import LatticeClient
from .entities import format_entity_for_lattice

logger = get_logger(__name__)


class LatticePublisher:
    """Publishes entity updates to Lattice with retry logic and metrics."""
    
    def __init__(
        self,
        client: LatticeClient,
        metrics: Optional[MetricsCollector] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        batch_size: int = 10,
        batch_timeout_seconds: float = 1.0,
    ):
        """
        Initialize Lattice publisher.
        
        Args:
            client: Lattice client instance
            metrics: Optional metrics collector
            max_retries: Maximum number of retry attempts
            retry_delay_seconds: Delay between retries
            batch_size: Number of entities to batch before publishing
            batch_timeout_seconds: Maximum time to wait before flushing batch
        """
        self.client = client
        self.metrics = metrics
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        
        self._batch: List[Dict] = []
        self._batch_start_time: Optional[float] = None
    
    def publish_entity(
        self,
        entity: Entity,
        sensor_reading: Optional[SensorReading] = None,
        sensor_id: Optional[str] = None,
    ) -> bool:
        """
        Publish a single entity update to Lattice.
        
        Args:
            entity: Entity to publish
            sensor_reading: Optional sensor reading
            sensor_id: Optional sensor ID
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            lattice_entity = format_entity_for_lattice(
                entity, sensor_reading, sensor_id
            )
            
            success = self._publish_with_retry(lattice_entity)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if self.metrics and sensor_id:
                if success:
                    self.metrics.record_message(sensor_id, latency_ms)
                else:
                    self.metrics.record_error(sensor_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing entity {entity.entity_id}: {e}")
            if self.metrics and sensor_id:
                self.metrics.record_error(sensor_id)
            return False
    
    def publish_entity_batch(
        self,
        entities: List[tuple[Entity, Optional[SensorReading], Optional[str]]],
    ) -> Dict[str, bool]:
        """
        Publish multiple entities in a batch.
        
        Args:
            entities: List of (entity, sensor_reading, sensor_id) tuples
            
        Returns:
            Dictionary mapping entity IDs to success status
        """
        lattice_entities = []
        
        for entity, sensor_reading, sensor_id in entities:
            try:
                lattice_entity = format_entity_for_lattice(
                    entity, sensor_reading, sensor_id
                )
                lattice_entities.append(lattice_entity)
            except Exception as e:
                logger.error(f"Error formatting entity {entity.entity_id}: {e}")
        
        if not lattice_entities:
            return {}
        
        start_time = time.time()
        results = self._publish_batch_with_retry(lattice_entities)
        latency_ms = (time.time() - start_time) * 1000
        
        # Update metrics for all sensors involved
        if self.metrics:
            sensor_ids = set()
            for entity, _, sensor_id in entities:
                if sensor_id:
                    sensor_ids.add(sensor_id)
            
            for sensor_id in sensor_ids:
                if sensor_id:
                    # Approximate latency per sensor
                    avg_latency = latency_ms / len(sensor_ids)
                    # Count successes and failures for this sensor
                    # (simplified - in reality would track per sensor)
                    self.metrics.record_message(sensor_id, avg_latency)
        
        return results
    
    def add_to_batch(
        self,
        entity: Entity,
        sensor_reading: Optional[SensorReading] = None,
        sensor_id: Optional[str] = None,
    ) -> Optional[Dict[str, bool]]:
        """
        Add entity to batch and publish if batch is full or timeout reached.
        
        Args:
            entity: Entity to add
            sensor_reading: Optional sensor reading
            sensor_id: Optional sensor ID
            
        Returns:
            Results dictionary if batch was published, None otherwise
        """
        if self._batch_start_time is None:
            self._batch_start_time = time.time()
        
        try:
            lattice_entity = format_entity_for_lattice(
                entity, sensor_reading, sensor_id
            )
            self._batch.append(lattice_entity)
        except Exception as e:
            logger.error(f"Error formatting entity {entity.entity_id}: {e}")
            return None
        
        # Check if batch should be published
        should_publish = False
        
        if len(self._batch) >= self.batch_size:
            should_publish = True
            logger.debug(f"Batch size reached ({self.batch_size}), publishing")
        
        if (
            self._batch_start_time
            and (time.time() - self._batch_start_time) >= self.batch_timeout_seconds
        ):
            should_publish = True
            logger.debug("Batch timeout reached, publishing")
        
        if should_publish:
            return self.flush_batch()
        
        return None
    
    def flush_batch(self) -> Dict[str, bool]:
        """
        Flush current batch to Lattice.
        
        Returns:
            Dictionary mapping entity IDs to success status
        """
        if not self._batch:
            return {}
        
        results = self._publish_batch_with_retry(self._batch)
        self._batch.clear()
        self._batch_start_time = None
        
        return results
    
    def _publish_with_retry(self, entity_data: Dict) -> bool:
        """
        Publish entity with retry logic.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                success = self.client.publish_entity(entity_data)
                if success:
                    return True
                
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Publish failed for {entity_data.get('id')}, "
                        f"retrying ({attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
                
            except Exception as e:
                logger.error(f"Exception during publish attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
        
        logger.error(f"Failed to publish entity {entity_data.get('id')} after {self.max_retries} attempts")
        return False
    
    def _publish_batch_with_retry(self, entities: List[Dict]) -> Dict[str, bool]:
        """
        Publish batch with retry logic.
        
        Args:
            entities: List of entity data dictionaries
            
        Returns:
            Dictionary mapping entity IDs to success status
        """
        for attempt in range(self.max_retries):
            try:
                results = self.client.publish_entities_batch(entities)
                
                # Check if all succeeded
                if all(results.values()):
                    return results
                
                # If some failed, retry failed ones
                failed_entities = [
                    e for e in entities if not results.get(e.get("id"), False)
                ]
                
                if attempt < self.max_retries - 1 and failed_entities:
                    logger.warning(
                        f"Batch publish partially failed, "
                        f"retrying {len(failed_entities)} entities "
                        f"({attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
                    entities = failed_entities
                else:
                    return results
                    
            except Exception as e:
                logger.error(f"Exception during batch publish attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
        
        # Return all as failed if we exhausted retries
        return {e.get("id", "unknown"): False for e in entities}

