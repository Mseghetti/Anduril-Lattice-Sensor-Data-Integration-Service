"""Acoustic sensor implementation."""

import random
import time
from typing import Dict, List

from ..simulation.entities import Entity
from ..utils.geo import add_noise_to_coordinate, calculate_distance
from .base import BaseSensor, SensorReading, SensorType


class AcousticSensor(BaseSensor):
    """Acoustic sensor for sound-based detection."""
    
    def __init__(
        self,
        sensor_id: str,
        position_lat: float,
        position_lon: float,
        position_altitude_m: float = 0.0,
        update_rate_hz: float = 10.0,  # Acoustic sensors can update frequently
        max_range_m: float = 5000.0,  # Short range for acoustic
        field_of_view_deg: float = 360.0,
        detection_accuracy_m: float = 100.0,  # Lower accuracy than other sensors
        ambient_noise_level: float = 0.5,  # Background noise level (0.0-1.0)
        wind_impact_factor: float = 1.0,  # Wind affects acoustic propagation
        metadata: Dict = None,
    ):
        """
        Initialize acoustic sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            position_lat: Sensor latitude
            position_lon: Sensor longitude
            position_altitude_m: Sensor altitude in meters
            update_rate_hz: Update rate in Hz
            max_range_m: Maximum detection range in meters
            field_of_view_deg: Field of view in degrees
            detection_accuracy_m: Position accuracy in meters
            ambient_noise_level: Background noise level (0.0-1.0)
            wind_impact_factor: Wind impact on detection (1.0 = no wind)
            metadata: Optional metadata dictionary
        """
        super().__init__(
            sensor_id=sensor_id,
            sensor_type=SensorType.ACOUSTIC,
            position_lat=position_lat,
            position_lon=position_lon,
            position_altitude_m=position_altitude_m,
            update_rate_hz=update_rate_hz,
            max_range_m=max_range_m,
            field_of_view_deg=field_of_view_deg,
            metadata=metadata,
        )
        self.detection_accuracy_m = detection_accuracy_m
        self.ambient_noise_level = ambient_noise_level
        self.wind_impact_factor = wind_impact_factor
    
    def _calculate_sound_level(self, entity: Entity) -> float:
        """
        Calculate estimated sound level from entity.
        
        Args:
            entity: Entity to calculate sound level for
            
        Returns:
            Estimated sound level (0.0-1.0)
        """
        # Sound level depends on entity type and speed
        base_sound = {
            "aircraft": 0.8,
            "ground_vehicle": 0.6,
            "maritime_vessel": 0.5,
            "unknown_contact": 0.4,
            "stationary_object": 0.1,
        }
        
        sound_level = base_sound.get(entity.entity_type.value, 0.3)
        
        # Speed affects sound (faster = louder)
        speed_factor = min(entity.speed_ms / 100.0, 1.5)
        sound_level *= speed_factor
        
        return min(sound_level, 1.0)
    
    def _calculate_detection_probability(self, entity: Entity) -> float:
        """
        Calculate probability of acoustic detection.
        
        Args:
            entity: Entity to calculate detection probability for
            
        Returns:
            Detection probability (0.0 to 1.0)
        """
        distance = calculate_distance(
            self.position_lat, self.position_lon, entity.lat, entity.lon
        )
        
        if distance > self.max_range_m:
            return 0.0
        
        # Acoustic detection depends on:
        # - Range (sound attenuates with distance)
        # - Sound level from entity
        # - Ambient noise
        # - Wind conditions
        
        sound_level = self._calculate_sound_level(entity)
        
        # Range attenuation (sound decreases with distance squared)
        range_factor = 1.0 / (1.0 + (distance / self.max_range_m) ** 2)
        
        # Signal-to-noise ratio
        snr = sound_level / max(self.ambient_noise_level, 0.1)
        snr_factor = min(snr / 2.0, 1.0)
        
        # Wind impact
        wind_factor = 1.0 / self.wind_impact_factor
        
        probability = range_factor * snr_factor * wind_factor
        
        return min(max(probability, 0.0), 1.0)
    
    def detect_entities(self, entities: List[Entity]) -> List[SensorReading]:
        """
        Detect entities via acoustic signatures.
        
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
            
            # Calculate detection probability
            detection_prob = self._calculate_detection_probability(entity)
            
            # Determine if entity is detected
            if random.random() < detection_prob:
                # Add measurement noise (acoustic sensors have lower accuracy)
                noisy_lat, noisy_lon = add_noise_to_coordinate(
                    entity.lat, entity.lon, self.detection_accuracy_m
                )
                
                distance = calculate_distance(
                    self.position_lat, self.position_lon, entity.lat, entity.lon
                )
                
                # Confidence based on detection probability and SNR
                sound_level = self._calculate_sound_level(entity)
                snr = sound_level / max(self.ambient_noise_level, 0.1)
                snr_factor = min(snr / 2.0, 1.0)
                confidence = detection_prob * snr_factor
                
                reading = SensorReading(
                    entity_id=entity.entity_id,
                    sensor_id=self.sensor_id,
                    timestamp=current_time,
                    position={
                        "lat": noisy_lat,
                        "lon": noisy_lon,
                        "altitude_m": entity.altitude_m + random.gauss(0, 50.0),
                    },
                    confidence=min(max(confidence, 0.0), 1.0),
                    metadata={
                        "sensor_type": "acoustic",
                        "range_m": distance,
                        "detection_accuracy_m": self.detection_accuracy_m,
                        "sound_level": sound_level,
                        "ambient_noise": self.ambient_noise_level,
                        "wind_factor": self.wind_impact_factor,
                    },
                )
                readings.append(reading)
        
        self.last_update = current_time
        return readings

