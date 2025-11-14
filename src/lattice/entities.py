"""Entity formatting for Lattice API."""

from typing import Dict, Optional

from ..simulation.entities import Entity, EntityType
from ..sensors.base import SensorReading
from ..utils.logging import get_logger

logger = get_logger(__name__)


def format_entity_for_lattice(
    entity: Entity,
    sensor_reading: Optional[SensorReading] = None,
    sensor_id: Optional[str] = None,
) -> Dict:
    """
    Format an entity for Lattice API submission.
    
    Args:
        entity: Entity to format
        sensor_reading: Optional sensor reading with detection data
        sensor_id: Optional sensor ID that detected the entity
        
    Returns:
        Dictionary formatted for Lattice Entities API
    """
    # Use sensor reading data if available, otherwise use entity data
    if sensor_reading:
        position = sensor_reading.position
        confidence = sensor_reading.confidence
        timestamp = sensor_reading.timestamp
        metadata = sensor_reading.metadata.copy()
    else:
        position = {
            "lat": entity.lat,
            "lon": entity.lon,
            "altitude_m": entity.altitude_m,
        }
        confidence = 1.0
        timestamp = entity.last_update
        metadata = {}
    
    # Map entity types to Lattice entity types
    lattice_entity_type_map = {
        "aircraft": "aircraft",
        "ground_vehicle": "ground_vehicle",
        "maritime_vessel": "maritime_vessel",
        "unknown_contact": "unknown_contact",
        "stationary_object": "stationary_object",
    }
    
    lattice_type = lattice_entity_type_map.get(
        entity.entity_type.value, "unknown_contact"
    )
    
    # Build Lattice entity structure
    # Note: This structure may need adjustment based on actual Lattice API schema
    lattice_entity = {
        "id": entity.entity_id,
        "type": lattice_type,
        "timestamp": timestamp,
        "position": {
            "latitude": position["lat"],
            "longitude": position["lon"],
            "altitude_meters": position.get("altitude_m", 0.0),
        },
        "motion": {
            "heading_degrees": entity.heading_deg,
            "speed_meters_per_second": entity.speed_ms,
        },
        "confidence": confidence,
        "metadata": {
            **entity.metadata,
            **metadata,
            "source_sensor": sensor_id or "unknown",
            "entity_type": entity.entity_type.value,
        },
    }
    
    return lattice_entity


def create_lattice_entity(
    entity_id: str,
    entity_type: str,
    position: Dict,
    motion: Optional[Dict] = None,
    confidence: float = 1.0,
    metadata: Optional[Dict] = None,
    timestamp: Optional[float] = None,
) -> Dict:
    """
    Create a Lattice entity dictionary from raw data.
    
    Args:
        entity_id: Unique entity identifier
        entity_type: Entity type string
        position: Position dictionary with lat, lon, altitude_m
        motion: Optional motion dictionary with heading_deg, speed_ms
        confidence: Detection confidence (0.0-1.0)
        metadata: Optional metadata dictionary
        timestamp: Optional timestamp (defaults to current time)
        
    Returns:
        Dictionary formatted for Lattice API
    """
    import time
    
    lattice_entity = {
        "id": entity_id,
        "type": entity_type,
        "timestamp": timestamp or time.time(),
        "position": {
            "latitude": position["lat"],
            "longitude": position["lon"],
            "altitude_meters": position.get("altitude_m", 0.0),
        },
        "confidence": confidence,
        "metadata": metadata or {},
    }
    
    if motion:
        lattice_entity["motion"] = {
            "heading_degrees": motion.get("heading_deg", 0.0),
            "speed_meters_per_second": motion.get("speed_ms", 0.0),
        }
    
    return lattice_entity

