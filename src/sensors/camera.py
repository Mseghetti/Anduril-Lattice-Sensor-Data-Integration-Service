"""EO/IR Camera sensor implementation."""

import random
import time
from typing import Dict, List

from ..simulation.entities import Entity
from ..utils.geo import add_noise_to_coordinate, calculate_distance
from .base import BaseSensor, SensorReading, SensorType


class CameraSensor(BaseSensor):
    """Electro-optical/Infrared camera sensor for visual detection."""
    
    def __init__(
        self,
        sensor_id: str,
        position_lat: float,
        position_lon: float,
        position_altitude_m: float = 0.0,
        update_rate_hz: float = 5.0,  # Cameras typically update faster
        max_range_m: float = 15000.0,  # Shorter range than radar
        field_of_view_deg: float = 60.0,  # Narrow FOV for cameras
        detection_accuracy_m: float = 20.0,
        weather_visibility_factor: float = 1.0,  # 1.0 = clear, <1.0 = reduced visibility
        day_night_mode: str = "auto",  # "day", "night", "auto"
        metadata: Dict = None,
    ):
        """
        Initialize camera sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            position_lat: Sensor latitude
            position_lon: Sensor longitude
            position_altitude_m: Sensor altitude in meters
            update_rate_hz: Update rate in Hz
            max_range_m: Maximum detection range in meters
            field_of_view_deg: Field of view in degrees
            detection_accuracy_m: Position accuracy in meters
            weather_visibility_factor: Weather impact on visibility (0.0-1.0)
            day_night_mode: Operating mode
            metadata: Optional metadata dictionary
        """
        super().__init__(
            sensor_id=sensor_id,
            sensor_type=SensorType.CAMERA,
            position_lat=position_lat,
            position_lon=position_lon,
            position_altitude_m=position_altitude_m,
            update_rate_hz=update_rate_hz,
            max_range_m=max_range_m,
            field_of_view_deg=field_of_view_deg,
            metadata=metadata,
        )
        self.detection_accuracy_m = detection_accuracy_m
        self.weather_visibility_factor = weather_visibility_factor
        self.day_night_mode = day_night_mode
    
    def _calculate_detection_probability(self, entity: Entity) -> float:
        """
        Calculate probability of visual detection.
        
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
        
        # Visual detection depends on:
        # - Range (closer = easier to see)
        # - Entity size/type
        # - Weather conditions
        # - Day/night conditions
        
        range_factor = 1.0 - (distance / self.max_range_m)
        
        # Entity type affects visibility
        visibility_by_type = {
            "aircraft": 0.9,
            "ground_vehicle": 0.7,
            "maritime_vessel": 0.8,
            "unknown_contact": 0.5,
            "stationary_object": 0.6,
        }
        type_factor = visibility_by_type.get(entity.entity_type.value, 0.5)
        
        # Weather impact
        weather_factor = self.weather_visibility_factor
        
        # Day/night impact (simplified)
        day_night_factor = 0.8 if self.day_night_mode == "night" else 1.0
        
        probability = range_factor * type_factor * weather_factor * day_night_factor
        
        return min(max(probability, 0.0), 1.0)
    
    def detect_entities(self, entities: List[Entity]) -> List[SensorReading]:
        """
        Detect entities via visual/IR imaging.
        
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
                # Add measurement noise (cameras have moderate accuracy)
                noisy_lat, noisy_lon = add_noise_to_coordinate(
                    entity.lat, entity.lon, self.detection_accuracy_m
                )
                
                distance = calculate_distance(
                    self.position_lat, self.position_lon, entity.lat, entity.lon
                )
                
                # Confidence based on detection probability and range
                range_factor = 1.0 - (distance / self.max_range_m) * 0.3
                confidence = detection_prob * range_factor
                
                reading = SensorReading(
                    entity_id=entity.entity_id,
                    sensor_id=self.sensor_id,
                    timestamp=current_time,
                    position={
                        "lat": noisy_lat,
                        "lon": noisy_lon,
                        "altitude_m": entity.altitude_m + random.gauss(0, 15.0),
                    },
                    confidence=min(max(confidence, 0.0), 1.0),
                    metadata={
                        "sensor_type": "camera",
                        "range_m": distance,
                        "detection_accuracy_m": self.detection_accuracy_m,
                        "weather_visibility": self.weather_visibility_factor,
                        "mode": self.day_night_mode,
                    },
                )
                readings.append(reading)
        
        self.last_update = current_time
        return readings

