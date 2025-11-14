"""ADS-B (Automatic Dependent Surveillance-Broadcast) sensor implementation."""

import random
import time
from typing import Dict, List

from ..simulation.entities import Entity
from ..utils.geo import add_noise_to_coordinate, calculate_distance
from .base import BaseSensor, SensorReading, SensorType


class ADSBSensor(BaseSensor):
    """ADS-B sensor that receives transponder broadcasts from aircraft."""
    
    def __init__(
        self,
        sensor_id: str,
        position_lat: float,
        position_lon: float,
        position_altitude_m: float = 0.0,
        update_rate_hz: float = 1.0,
        max_range_m: float = 200000.0,  # ADS-B has longer range than radar
        field_of_view_deg: float = 360.0,
        reception_accuracy_m: float = 10.0,  # ADS-B is very accurate
        transponder_coverage: float = 0.95,  # Fraction of aircraft with transponders
        metadata: Dict = None,
    ):
        """
        Initialize ADS-B sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            position_lat: Sensor latitude
            position_lon: Sensor longitude
            position_altitude_m: Sensor altitude in meters
            update_rate_hz: Update rate in Hz
            max_range_m: Maximum reception range in meters
            field_of_view_deg: Field of view in degrees
            reception_accuracy_m: Position accuracy in meters
            transponder_coverage: Fraction of aircraft with working transponders
            metadata: Optional metadata dictionary
        """
        super().__init__(
            sensor_id=sensor_id,
            sensor_type=SensorType.ADSB,
            position_lat=position_lat,
            position_lon=position_lon,
            position_altitude_m=position_altitude_m,
            update_rate_hz=update_rate_hz,
            max_range_m=max_range_m,
            field_of_view_deg=field_of_view_deg,
            metadata=metadata,
        )
        self.reception_accuracy_m = reception_accuracy_m
        self.transponder_coverage = transponder_coverage
    
    def _has_transponder(self, entity: Entity) -> bool:
        """
        Check if entity has a working transponder.
        
        Args:
            entity: Entity to check
            
        Returns:
            True if entity has transponder
        """
        # Only aircraft typically have ADS-B transponders
        if entity.entity_type.value != "aircraft":
            return False
        
        # Check transponder coverage probability
        return random.random() < self.transponder_coverage
    
    def detect_entities(self, entities: List[Entity]) -> List[SensorReading]:
        """
        Detect entities via ADS-B transponder broadcasts.
        
        Args:
            entities: List of entities to check for detection
            
        Returns:
            List of sensor readings
        """
        if not self.should_update():
            return []
        
        readings: List[SensorReading] = []
        current_time = time.time()
        
        for entity in entities:
            if not self.can_detect(entity):
                continue
            
            # Only detect if entity has transponder
            if not self._has_transponder(entity):
                continue
            
            # ADS-B provides very accurate position data
            # Add minimal noise (much less than radar)
            noisy_lat, noisy_lon = add_noise_to_coordinate(
                entity.lat, entity.lon, self.reception_accuracy_m
            )
            
            distance = calculate_distance(
                self.position_lat, self.position_lon, entity.lat, entity.lon
            )
            
            # ADS-B typically has high confidence
            # Confidence decreases slightly with range
            range_factor = 1.0 - (distance / self.max_range_m) * 0.1
            confidence = min(max(range_factor, 0.85), 1.0)
            
            reading = SensorReading(
                entity_id=entity.entity_id,
                sensor_id=self.sensor_id,
                timestamp=current_time,
                position={
                    "lat": noisy_lat,
                    "lon": noisy_lon,
                    "altitude_m": entity.altitude_m + random.gauss(0, 5.0),
                },
                confidence=confidence,
                metadata={
                    "sensor_type": "adsb",
                    "range_m": distance,
                    "transponder_id": f"ADSB_{entity.entity_id}",
                    "reception_accuracy_m": self.reception_accuracy_m,
                    "speed_ms": entity.speed_ms,
                    "heading_deg": entity.heading_deg,
                },
            )
            readings.append(reading)
        
        self.last_update = current_time
        return readings

