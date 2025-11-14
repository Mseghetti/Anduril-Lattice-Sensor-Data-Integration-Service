"""Base sensor class and sensor type enumeration."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from ..simulation.entities import Entity
from ..utils.geo import calculate_distance, is_within_range


class SensorType(str, Enum):
    """Sensor type enumeration."""
    
    RADAR = "radar"
    ADSB = "adsb"
    CAMERA = "camera"
    ACOUSTIC = "acoustic"


@dataclass
class SensorReading:
    """Represents a sensor reading/detection."""
    
    entity_id: str
    sensor_id: str
    timestamp: float
    position: Dict[str, float]  # lat, lon, altitude_m
    confidence: float  # 0.0 to 1.0
    metadata: Dict = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class BaseSensor(ABC):
    """Abstract base class for all sensors."""
    
    def __init__(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        position_lat: float,
        position_lon: float,
        position_altitude_m: float = 0.0,
        update_rate_hz: float = 1.0,
        max_range_m: float = 10000.0,
        field_of_view_deg: float = 360.0,
        metadata: Optional[Dict] = None,
    ):
        """
        Initialize base sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            sensor_type: Type of sensor
            position_lat: Sensor latitude
            position_lon: Sensor longitude
            position_altitude_m: Sensor altitude in meters
            update_rate_hz: Update rate in Hz
            max_range_m: Maximum detection range in meters
            field_of_view_deg: Field of view in degrees (360 = omnidirectional)
            metadata: Optional metadata dictionary
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.position_lat = position_lat
        self.position_lon = position_lon
        self.position_altitude_m = position_altitude_m
        self.update_rate_hz = update_rate_hz
        self.max_range_m = max_range_m
        self.field_of_view_deg = field_of_view_deg
        self.metadata = metadata or {}
        self.last_update = 0.0
        self.is_active = True
        self.health_status = "operational"
    
    def can_detect(self, entity: Entity) -> bool:
        """
        Check if sensor can detect an entity.
        
        Args:
            entity: Entity to check
            
        Returns:
            True if entity is within range and field of view
        """
        if not self.is_active:
            return False
        
        # Check range
        distance = calculate_distance(
            self.position_lat,
            self.position_lon,
            entity.lat,
            entity.lon,
        )
        if distance > self.max_range_m:
            return False
        
        # Check field of view (simplified - assumes omnidirectional if 360)
        if self.field_of_view_deg < 360:
            # TODO: Implement proper FOV check based on sensor heading
            pass
        
        return True
    
    def should_update(self) -> bool:
        """Check if sensor should update based on update rate."""
        current_time = time.time()
        time_since_update = current_time - self.last_update
        min_interval = 1.0 / self.update_rate_hz
        return time_since_update >= min_interval
    
    @abstractmethod
    def detect_entities(self, entities: List[Entity]) -> List[SensorReading]:
        """
        Detect entities and generate sensor readings.
        
        Args:
            entities: List of entities to check for detection
            
        Returns:
            List of sensor readings
        """
        pass
    
    def get_status(self) -> Dict:
        """Get sensor status information."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "position": {
                "lat": self.position_lat,
                "lon": self.position_lon,
                "altitude_m": self.position_altitude_m,
            },
            "update_rate_hz": self.update_rate_hz,
            "max_range_m": self.max_range_m,
            "field_of_view_deg": self.field_of_view_deg,
            "is_active": self.is_active,
            "health_status": self.health_status,
            "last_update": self.last_update,
        }
    
    def set_active(self, active: bool) -> None:
        """Set sensor active/inactive state."""
        self.is_active = active
    
    def set_health_status(self, status: str) -> None:
        """Set sensor health status."""
        self.health_status = status

