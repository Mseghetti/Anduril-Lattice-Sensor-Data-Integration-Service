"""Simulation engine that orchestrates sensors, entities, and Lattice publishing."""

import asyncio
import time
from typing import Dict, List, Optional

from ..lattice.publisher import LatticePublisher
from ..sensors.base import BaseSensor, SensorReading
from ..simulation.entities import Entity
from ..utils.logging import get_logger
from ..utils.metrics import MetricsCollector

logger = get_logger(__name__)


class SimulationEngine:
    """Main simulation engine that orchestrates the entire simulation."""
    
    def __init__(
        self,
        sensors: List[BaseSensor],
        entities: List[Entity],
        publisher: Optional[LatticePublisher] = None,
        metrics: Optional[MetricsCollector] = None,
        simulation_speed: float = 1.0,
        update_rate_hz: float = 10.0,
    ):
        """
        Initialize simulation engine.
        
        Args:
            sensors: List of sensor instances
            entities: List of entity instances
            publisher: Optional Lattice publisher
            metrics: Optional metrics collector
            simulation_speed: Simulation speed multiplier (1.0 = real-time)
            update_rate_hz: Main loop update rate in Hz
        """
        self.sensors = sensors
        self.entities = entities
        self.publisher = publisher
        self.metrics = metrics
        self.simulation_speed = simulation_speed
        self.update_rate_hz = update_rate_hz
        
        self.is_running = False
        self.last_update_time = time.time()
        self.start_time = time.time()
        
        # Track entity states
        self.entity_states: Dict[str, Dict] = {}
        
        logger.info(
            f"Simulation engine initialized with {len(sensors)} sensors "
            f"and {len(entities)} entities"
        )
    
    def add_sensor(self, sensor: BaseSensor) -> None:
        """Add a sensor to the simulation."""
        self.sensors.append(sensor)
        logger.info(f"Added sensor: {sensor.sensor_id}")
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the simulation."""
        self.entities.append(entity)
        logger.info(f"Added entity: {entity.entity_id}")
    
    def remove_entity(self, entity_id: str) -> bool:
        """
        Remove an entity from the simulation.
        
        Args:
            entity_id: ID of entity to remove
            
        Returns:
            True if entity was found and removed
        """
        for i, entity in enumerate(self.entities):
            if entity.entity_id == entity_id:
                self.entities.pop(i)
                self.entity_states.pop(entity_id, None)
                logger.info(f"Removed entity: {entity_id}")
                return True
        return False
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None
    
    def step(self, delta_time: float) -> None:
        """
        Execute one simulation step.
        
        Args:
            delta_time: Time elapsed since last step in seconds
        """
        current_time = time.time()
        
        # Update all entities based on their movement patterns
        for entity in self.entities:
            entity.step(delta_time)
        
        # Update sensors and collect readings
        all_readings: List[tuple[Entity, SensorReading, str]] = []
        
        for sensor in self.sensors:
            if not sensor.is_active:
                continue
            
            try:
                readings = sensor.detect_entities(self.entities)
                
                for reading in readings:
                    # Find the entity for this reading
                    entity = self.get_entity(reading.entity_id)
                    if entity:
                        all_readings.append((entity, reading, sensor.sensor_id))
            except Exception as e:
                logger.error(f"Error in sensor {sensor.sensor_id}: {e}")
                if self.metrics:
                    self.metrics.record_error(sensor.sensor_id)
        
        # Publish to Lattice
        if self.publisher:
            if len(all_readings) > 1:
                # Use batch publishing for multiple readings
                self.publisher.publish_entity_batch(all_readings)
            else:
                # Publish individually
                for entity, reading, sensor_id in all_readings:
                    self.publisher.publish_entity(entity, reading, sensor_id)
        
        # Update metrics
        if self.metrics:
            self.metrics.update_entity_counts(len(self.entities), len(self.entities))
        
        self.last_update_time = current_time
    
    def run(self, duration_seconds: Optional[float] = None) -> None:
        """
        Run the simulation synchronously.
        
        Args:
            duration_seconds: Optional duration to run (None = run indefinitely)
        """
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        
        logger.info("Starting simulation...")
        
        try:
            while self.is_running:
                current_time = time.time()
                real_delta = current_time - self.last_update_time
                simulation_delta = real_delta * self.simulation_speed
                
                # Execute simulation step
                self.step(simulation_delta)
                
                # Check duration limit
                if duration_seconds:
                    elapsed = current_time - self.start_time
                    if elapsed >= duration_seconds:
                        logger.info(f"Simulation duration limit reached ({duration_seconds}s)")
                        break
                
                # Sleep to maintain update rate
                sleep_time = (1.0 / self.update_rate_hz) - (time.time() - current_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        finally:
            self.stop()
    
    async def run_async(self, duration_seconds: Optional[float] = None) -> None:
        """
        Run the simulation asynchronously.
        
        Args:
            duration_seconds: Optional duration to run (None = run indefinitely)
        """
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = time.time()
        
        logger.info("Starting async simulation...")
        
        try:
            while self.is_running:
                current_time = time.time()
                real_delta = current_time - self.last_update_time
                simulation_delta = real_delta * self.simulation_speed
                
                # Execute simulation step
                self.step(simulation_delta)
                
                # Check duration limit
                if duration_seconds:
                    elapsed = current_time - self.start_time
                    if elapsed >= duration_seconds:
                        logger.info(f"Simulation duration limit reached ({duration_seconds}s)")
                        break
                
                # Sleep to maintain update rate
                sleep_time = (1.0 / self.update_rate_hz) - (time.time() - current_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
        except asyncio.CancelledError:
            logger.info("Simulation cancelled")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the simulation."""
        if self.is_running:
            self.is_running = False
            
            # Flush any pending batch publishes
            if self.publisher:
                self.publisher.flush_batch()
            
            elapsed = time.time() - self.start_time
            logger.info(f"Simulation stopped. Total runtime: {elapsed:.2f}s")
    
    def get_status(self) -> Dict:
        """Get current simulation status."""
        return {
            "is_running": self.is_running,
            "num_sensors": len(self.sensors),
            "num_entities": len(self.entities),
            "simulation_speed": self.simulation_speed,
            "update_rate_hz": self.update_rate_hz,
            "runtime_seconds": time.time() - self.start_time if self.is_running else 0,
            "sensors": [s.get_status() for s in self.sensors],
        }
    
    def get_entity_summary(self) -> List[Dict]:
        """Get summary of all entities."""
        return [entity.to_dict() for entity in self.entities]

