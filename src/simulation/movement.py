"""Movement pattern algorithms for entities."""

import math
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from ..utils.geo import calculate_bearing, calculate_destination, calculate_distance

if TYPE_CHECKING:
    from .entities import Entity


class MovementPattern(ABC):
    """Abstract base class for movement patterns."""
    
    @abstractmethod
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """
        Update entity state based on movement pattern.
        
        Args:
            current_lat: Current latitude
            current_lon: Current longitude
            current_altitude_m: Current altitude in meters
            current_heading_deg: Current heading in degrees
            current_speed_ms: Current speed in meters per second
            delta_time: Time elapsed since last update in seconds
            
        Returns:
            Dictionary with updated state: {
                "lat": float,
                "lon": float,
                "altitude_m": float,
                "heading_deg": float,
                "speed_ms": float
            }
        """
        pass


class WaypointPattern(MovementPattern):
    """Waypoint navigation pattern."""
    
    def __init__(
        self,
        waypoints: List[Tuple[float, float, Optional[float]]],
        speed_ms: float = 50.0,
        arrival_threshold_m: float = 100.0,
        loop: bool = False,
    ):
        """
        Initialize waypoint pattern.
        
        Args:
            waypoints: List of (lat, lon, optional_altitude) tuples
            speed_ms: Speed in meters per second
            arrival_threshold_m: Distance threshold to consider waypoint reached
            loop: Whether to loop back to first waypoint after last
        """
        self.waypoints = waypoints
        self.speed_ms = speed_ms
        self.arrival_threshold_m = arrival_threshold_m
        self.loop = loop
        self.current_waypoint_idx = 0
    
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """Update position moving toward current waypoint."""
        if not self.waypoints:
            return {
                "lat": current_lat,
                "lon": current_lon,
                "altitude_m": current_altitude_m,
                "heading_deg": current_heading_deg,
                "speed_ms": 0.0,
            }
        
        target_lat, target_lon, target_alt = self.waypoints[self.current_waypoint_idx]
        if target_alt is None:
            target_alt = current_altitude_m
        
        distance = calculate_distance(current_lat, current_lon, target_lat, target_lon)
        
        # Check if waypoint reached
        if distance <= self.arrival_threshold_m:
            # Move to next waypoint
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.waypoints):
                if self.loop:
                    self.current_waypoint_idx = 0
                else:
                    # Stay at last waypoint
                    self.current_waypoint_idx = len(self.waypoints) - 1
                    return {
                        "lat": target_lat,
                        "lon": target_lon,
                        "altitude_m": target_alt,
                        "heading_deg": current_heading_deg,
                        "speed_ms": 0.0,
                    }
            target_lat, target_lon, target_alt = self.waypoints[self.current_waypoint_idx]
            if target_alt is None:
                target_alt = current_altitude_m
        
        # Calculate bearing to target
        bearing = calculate_bearing(current_lat, current_lon, target_lat, target_lon)
        
        # Move toward waypoint
        distance_to_move = min(self.speed_ms * delta_time, distance)
        new_lat, new_lon = calculate_destination(
            current_lat, current_lon, bearing, distance_to_move
        )
        
        # Smooth altitude change
        alt_diff = target_alt - current_altitude_m
        alt_change_rate = 10.0  # m/s
        alt_change = min(abs(alt_diff), alt_change_rate * delta_time) * (1 if alt_diff > 0 else -1)
        new_alt = current_altitude_m + alt_change
        
        return {
            "lat": new_lat,
            "lon": new_lon,
            "altitude_m": new_alt,
            "heading_deg": bearing,
            "speed_ms": self.speed_ms,
        }


class PatrolPattern(MovementPattern):
    """Patrol pattern (circular, racetrack, figure-8)."""
    
    def __init__(
        self,
        center_lat: float,
        center_lon: float,
        pattern_type: str = "circular",  # circular, racetrack, figure8
        radius_m: float = 5000.0,
        speed_ms: float = 50.0,
        altitude_m: float = 1000.0,
    ):
        """
        Initialize patrol pattern.
        
        Args:
            center_lat: Center latitude of patrol area
            center_lon: Center longitude of patrol area
            pattern_type: Type of patrol (circular, racetrack, figure8)
            radius_m: Radius of patrol area in meters
            speed_ms: Speed in meters per second
            altitude_m: Altitude in meters
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.pattern_type = pattern_type
        self.radius_m = radius_m
        self.speed_ms = speed_ms
        self.altitude_m = altitude_m
        self.angle = 0.0  # Current angle in radians
    
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """Update position following patrol pattern."""
        angular_velocity = self.speed_ms / self.radius_m  # rad/s
        
        if self.pattern_type == "circular":
            self.angle += angular_velocity * delta_time
            offset_lat = self.radius_m / 111000.0 * math.cos(self.angle)
            offset_lon = self.radius_m / (111000.0 * math.cos(math.radians(self.center_lat))) * math.sin(self.angle)
            new_lat = self.center_lat + offset_lat
            new_lon = self.center_lon + offset_lon
            heading = (math.degrees(self.angle) + 90) % 360
        
        elif self.pattern_type == "racetrack":
            # Simplified racetrack: two semicircles connected by straight segments
            period = 2 * math.pi * self.radius_m / self.speed_ms
            t = (self.angle * period / (2 * math.pi)) % period
            if t < period / 4 or t > 3 * period / 4:
                # Straight segment
                self.angle += angular_velocity * delta_time
                offset_lat = self.radius_m / 111000.0 * math.cos(self.angle)
                offset_lon = self.radius_m / (111000.0 * math.cos(math.radians(self.center_lat))) * math.sin(self.angle)
            else:
                # Circular segment
                self.angle += angular_velocity * delta_time
                offset_lat = self.radius_m / 111000.0 * math.cos(self.angle)
                offset_lon = self.radius_m / (111000.0 * math.cos(math.radians(self.center_lat))) * math.sin(self.angle)
            new_lat = self.center_lat + offset_lat
            new_lon = self.center_lon + offset_lon
            heading = (math.degrees(self.angle) + 90) % 360
        
        else:  # figure8
            # Figure-8 pattern
            self.angle += angular_velocity * delta_time
            offset_lat = self.radius_m / 111000.0 * math.sin(self.angle)
            offset_lon = self.radius_m / (111000.0 * math.cos(math.radians(self.center_lat))) * math.sin(2 * self.angle)
            new_lat = self.center_lat + offset_lat
            new_lon = self.center_lon + offset_lon
            heading = (math.degrees(self.angle) + 90) % 360
        
        return {
            "lat": new_lat,
            "lon": new_lon,
            "altitude_m": self.altitude_m,
            "heading_deg": heading,
            "speed_ms": self.speed_ms,
        }


class RandomWalkPattern(MovementPattern):
    """Random walk pattern with constraints."""
    
    def __init__(
        self,
        initial_lat: float,
        initial_lon: float,
        speed_ms: float = 30.0,
        max_deviation_deg: float = 45.0,
        boundary_radius_m: Optional[float] = None,
        altitude_m: float = 1000.0,
    ):
        """
        Initialize random walk pattern.
        
        Args:
            initial_lat: Initial latitude
            initial_lon: Initial longitude
            speed_ms: Speed in meters per second
            max_deviation_deg: Maximum heading change per update in degrees
            boundary_radius_m: Optional maximum distance from initial point
            altitude_m: Altitude in meters
        """
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.speed_ms = speed_ms
        self.max_deviation_deg = max_deviation_deg
        self.boundary_radius_m = boundary_radius_m
        self.altitude_m = altitude_m
        self.current_heading = random.uniform(0, 360)
    
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """Update position with random walk."""
        # Random heading change
        heading_change = random.uniform(-self.max_deviation_deg, self.max_deviation_deg)
        self.current_heading = (self.current_heading + heading_change) % 360
        
        # Move in current heading direction
        distance = self.speed_ms * delta_time
        new_lat, new_lon = calculate_destination(
            current_lat, current_lon, self.current_heading, distance
        )
        
        # Check boundary constraint
        if self.boundary_radius_m:
            dist_from_origin = calculate_distance(
                self.initial_lat, self.initial_lon, new_lat, new_lon
            )
            if dist_from_origin > self.boundary_radius_m:
                # Turn back toward origin
                bearing_to_origin = calculate_bearing(
                    new_lat, new_lon, self.initial_lat, self.initial_lon
                )
                self.current_heading = bearing_to_origin
                new_lat, new_lon = calculate_destination(
                    current_lat, current_lon, self.current_heading, distance
                )
        
        return {
            "lat": new_lat,
            "lon": new_lon,
            "altitude_m": self.altitude_m,
            "heading_deg": self.current_heading,
            "speed_ms": self.speed_ms,
        }


class FormationPattern(MovementPattern):
    """Formation flying pattern (maintains relative position to leader)."""
    
    def __init__(
        self,
        leader_entity: "Entity",  # Forward reference
        offset_lat_m: float = 0.0,
        offset_lon_m: float = 0.0,
        offset_altitude_m: float = 0.0,
    ):
        """
        Initialize formation pattern.
        
        Args:
            leader_entity: Entity to follow
            offset_lat_m: Offset in meters (north positive)
            offset_lon_m: Offset in meters (east positive)
            offset_altitude_m: Altitude offset in meters
        """
        self.leader_entity = leader_entity
        self.offset_lat_m = offset_lat_m
        self.offset_lon_m = offset_lon_m
        self.offset_altitude_m = offset_altitude_m
    
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """Update position to maintain formation."""
        leader = self.leader_entity
        
        # Calculate offset position relative to leader
        # Convert meters to degrees (approximate)
        offset_lat_deg = self.offset_lat_m / 111000.0
        offset_lon_deg = self.offset_lon_m / (111000.0 * math.cos(math.radians(leader.lat)))
        
        new_lat = leader.lat + offset_lat_deg
        new_lon = leader.lon + offset_lon_deg
        new_alt = leader.altitude_m + self.offset_altitude_m
        
        # Match leader's heading and speed
        heading = leader.heading_deg
        speed = leader.speed_ms
        
        return {
            "lat": new_lat,
            "lon": new_lon,
            "altitude_m": new_alt,
            "heading_deg": heading,
            "speed_ms": speed,
        }


class EvasivePattern(MovementPattern):
    """Evasive maneuvers pattern."""
    
    def __init__(
        self,
        base_speed_ms: float = 100.0,
        maneuver_probability: float = 0.1,
        max_altitude_change_m: float = 500.0,
        max_heading_change_deg: float = 90.0,
    ):
        """
        Initialize evasive pattern.
        
        Args:
            base_speed_ms: Base speed in meters per second
            maneuver_probability: Probability of evasive maneuver per update
            max_altitude_change_m: Maximum altitude change in meters
            max_heading_change_deg: Maximum heading change in degrees
        """
        self.base_speed_ms = base_speed_ms
        self.maneuver_probability = maneuver_probability
        self.max_altitude_change_m = max_altitude_change_m
        self.max_heading_change_deg = max_heading_change_deg
        self.in_maneuver = False
        self.maneuver_end_time = 0.0
    
    def update(
        self,
        current_lat: float,
        current_lon: float,
        current_altitude_m: float,
        current_heading_deg: float,
        current_speed_ms: float,
        delta_time: float,
    ) -> Dict:
        """Update position with potential evasive maneuvers."""
        import time
        
        current_time = time.time()
        
        # Check if we should start a new maneuver
        if not self.in_maneuver and random.random() < self.maneuver_probability:
            self.in_maneuver = True
            self.maneuver_end_time = current_time + random.uniform(2.0, 5.0)  # 2-5 second maneuver
        
        # Execute maneuver
        if self.in_maneuver:
            if current_time < self.maneuver_end_time:
                # Random heading and altitude change
                heading_change = random.uniform(
                    -self.max_heading_change_deg, self.max_heading_change_deg
                )
                new_heading = (current_heading_deg + heading_change) % 360
                
                altitude_change = random.uniform(
                    -self.max_altitude_change_m, self.max_altitude_change_m
                )
                new_altitude = max(0, current_altitude_m + altitude_change * delta_time)
                
                # Increase speed during maneuver
                speed = self.base_speed_ms * 1.5
            else:
                # End maneuver
                self.in_maneuver = False
                new_heading = current_heading_deg
                new_altitude = current_altitude_m
                speed = self.base_speed_ms
        else:
            # Normal movement
            new_heading = current_heading_deg
            new_altitude = current_altitude_m
            speed = self.base_speed_ms
        
        # Move in current direction
        distance = speed * delta_time
        new_lat, new_lon = calculate_destination(
            current_lat, current_lon, new_heading, distance
        )
        
        return {
            "lat": new_lat,
            "lon": new_lon,
            "altitude_m": new_altitude,
            "heading_deg": new_heading,
            "speed_ms": speed,
        }

