"""Entity models for simulation."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .movement import MovementPattern


class EntityType(str, Enum):
    """Entity type enumeration."""
    
    AIRCRAFT = "aircraft"
    GROUND_VEHICLE = "ground_vehicle"
    MARITIME_VESSEL = "maritime_vessel"
    UNKNOWN_CONTACT = "unknown_contact"
    STATIONARY_OBJECT = "stationary_object"


@dataclass
class Entity:
    """Represents a simulated entity (aircraft, vehicle, vessel, etc.)."""
    
    entity_id: str
    entity_type: EntityType
    lat: float
    lon: float
    altitude_m: float = 0.0
    heading_deg: float = 0.0
    speed_ms: float = 0.0
    movement_pattern: Optional[MovementPattern] = None
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    
    def update_position(
        self, lat: float, lon: float, altitude_m: Optional[float] = None
    ) -> None:
        """Update entity position."""
        self.lat = lat
        self.lon = lon
        if altitude_m is not None:
            self.altitude_m = altitude_m
        self.last_update = time.time()
    
    def update_motion(
        self, heading_deg: float, speed_ms: float
    ) -> None:
        """Update entity motion parameters."""
        self.heading_deg = heading_deg
        self.speed_ms = speed_ms
        self.last_update = time.time()
    
    def to_dict(self) -> Dict:
        """Convert entity to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "position": {
                "lat": self.lat,
                "lon": self.lon,
                "altitude_m": self.altitude_m,
            },
            "motion": {
                "heading_deg": self.heading_deg,
                "speed_ms": self.speed_ms,
            },
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_update": self.last_update,
        }
    
    def step(self, delta_time: float) -> None:
        """Update entity state based on movement pattern."""
        if self.movement_pattern:
            new_state = self.movement_pattern.update(
                self.lat, self.lon, self.altitude_m, self.heading_deg, self.speed_ms, delta_time
            )
            self.update_position(new_state["lat"], new_state["lon"], new_state.get("altitude_m"))
            self.update_motion(new_state["heading_deg"], new_state["speed_ms"])


def create_entity(
    entity_id: str,
    entity_type: EntityType,
    initial_lat: float,
    initial_lon: float,
    initial_altitude_m: float = 0.0,
    initial_heading_deg: float = 0.0,
    initial_speed_ms: float = 0.0,
    movement_pattern: Optional[MovementPattern] = None,
    metadata: Optional[Dict] = None,
) -> Entity:
    """
    Create a new entity with specified parameters.
    
    Args:
        entity_id: Unique identifier for the entity
        entity_type: Type of entity
        initial_lat: Initial latitude
        initial_lon: Initial longitude
        initial_altitude_m: Initial altitude in meters
        initial_heading_deg: Initial heading in degrees
        initial_speed_ms: Initial speed in meters per second
        movement_pattern: Optional movement pattern
        metadata: Optional metadata dictionary
        
    Returns:
        Created Entity instance
    """
    return Entity(
        entity_id=entity_id,
        entity_type=entity_type,
        lat=initial_lat,
        lon=initial_lon,
        altitude_m=initial_altitude_m,
        heading_deg=initial_heading_deg,
        speed_ms=initial_speed_ms,
        movement_pattern=movement_pattern,
        metadata=metadata or {},
    )

