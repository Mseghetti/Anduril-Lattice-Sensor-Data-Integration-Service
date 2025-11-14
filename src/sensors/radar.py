"""Radar sensor implementation."""

import random
import time
from typing import Dict, List

from ..simulation.entities import Entity
from ..utils.geo import add_noise_to_coordinate, calculate_distance
from .base import BaseSensor, SensorReading, SensorType


class RadarSensor(BaseSensor):
    """Radar sensor that detects entities based on range and radar cross-section."""
    
    def __init__(
        self,
        sensor_id: str,
        position_lat: float,
        position_lon: float,
        position_altitude_m: float = 0.0,
        update_rate_hz: float = 1.0,
        max_range_m: float = 50000.0,
        field_of_view_deg: float = 360.0,
        min_detectable_rcs_m2: float = 0.1,  # Minimum radar cross-section in m²
        range_accuracy_m: float = 50.0,  # Range measurement accuracy
        angle_accuracy_deg: float = 0.5,  # Angular accuracy
        false_alarm_rate: float = 0.01,  # Probability of false detection
        metadata: Dict = None,
    ):
        """
        Initialize radar sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            position_lat: Sensor latitude
            position_lon: Sensor longitude
            position_altitude_m: Sensor altitude in meters
            update_rate_hz: Update rate in Hz
            max_range_m: Maximum detection range in meters
            field_of_view_deg: Field of view in degrees
            min_detectable_rcs_m2: Minimum detectable radar cross-section
            range_accuracy_m: Range measurement accuracy in meters
            angle_accuracy_deg: Angular accuracy in degrees
            false_alarm_rate: Probability of false alarm per update
            metadata: Optional metadata dictionary
        """
        super().__init__(
            sensor_id=sensor_id,
            sensor_type=SensorType.RADAR,
            position_lat=position_lat,
            position_lon=position_lon,
            position_altitude_m=position_altitude_m,
            update_rate_hz=update_rate_hz,
            max_range_m=max_range_m,
            field_of_view_deg=field_of_view_deg,
            metadata=metadata,
        )
        self.min_detectable_rcs_m2 = min_detectable_rcs_m2
        self.range_accuracy_m = range_accuracy_m
        self.angle_accuracy_deg = angle_accuracy_deg
        self.false_alarm_rate = false_alarm_rate
    
    def _calculate_radar_cross_section(self, entity: Entity) -> float:
        """
        Calculate estimated radar cross-section for an entity.
        
        Args:
            entity: Entity to calculate RCS for
            
        Returns:
            Estimated RCS in m²
        """
        # Simplified RCS model based on entity type
        base_rcs = {
            "aircraft": 10.0,  # m²
            "ground_vehicle": 5.0,
            "maritime_vessel": 100.0,
            "unknown_contact": 1.0,
            "stationary_object": 50.0,
        }
        
        rcs = base_rcs.get(entity.entity_type.value, 1.0)
        
        # Adjust for distance (simplified atmospheric attenuation)
        distance = calculate_distance(
            self.position_lat, self.position_lon, entity.lat, entity.lon
        )
        if distance > 10000:
            rcs *= 0.8  # Reduced RCS at long range
        
        return rcs
    
    def _calculate_detection_probability(self, entity: Entity) -> float:
        """
        Calculate probability of detection based on range and RCS.
        
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
        
        rcs = self._calculate_radar_cross_section(entity)
        if rcs < self.min_detectable_rcs_m2:
            return 0.0
        
        # Simplified detection probability model
        # Probability decreases with range and increases with RCS
        range_factor = 1.0 - (distance / self.max_range_m)
        rcs_factor = min(rcs / self.min_detectable_rcs_m2, 2.0) / 2.0
        
        probability = range_factor * rcs_factor
        
        # Add some randomness for realistic behavior
        probability *= random.uniform(0.9, 1.0)
        
        return min(max(probability, 0.0), 1.0)
    
    def detect_entities(self, entities: List[Entity]) -> List[SensorReading]:
        """
        Detect entities and generate radar readings.
        
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
                # Add measurement noise
                noisy_lat, noisy_lon = add_noise_to_coordinate(
                    entity.lat, entity.lon, self.range_accuracy_m
                )
                
                # Calculate confidence based on detection probability and range
                distance = calculate_distance(
                    self.position_lat, self.position_lon, entity.lat, entity.lon
                )
                range_factor = 1.0 - (distance / self.max_range_m)
                confidence = detection_prob * range_factor
                
                reading = SensorReading(
                    entity_id=entity.entity_id,
                    sensor_id=self.sensor_id,
                    timestamp=current_time,
                    position={
                        "lat": noisy_lat,
                        "lon": noisy_lon,
                        "altitude_m": entity.altitude_m + random.gauss(0, 10.0),
                    },
                    confidence=min(max(confidence, 0.0), 1.0),
                    metadata={
                        "sensor_type": "radar",
                        "range_m": distance,
                        "rcs_m2": self._calculate_radar_cross_section(entity),
                        "range_accuracy_m": self.range_accuracy_m,
                        "angle_accuracy_deg": self.angle_accuracy_deg,
                    },
                )
                readings.append(reading)
        
        # Simulate false alarms
        if random.random() < self.false_alarm_rate:
            # Generate false alarm at random position within range
            false_lat = self.position_lat + random.uniform(-0.01, 0.01)
            false_lon = self.position_lon + random.uniform(-0.01, 0.01)
            
            false_reading = SensorReading(
                entity_id=f"false_alarm_{int(current_time)}",
                sensor_id=self.sensor_id,
                timestamp=current_time,
                position={
                    "lat": false_lat,
                    "lon": false_lon,
                    "altitude_m": random.uniform(0, 10000),
                },
                confidence=random.uniform(0.1, 0.3),
                metadata={
                    "sensor_type": "radar",
                    "false_alarm": True,
                },
            )
            readings.append(false_reading)
        
        self.last_update = current_time
        return readings

