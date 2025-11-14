"""Geographic calculation utilities."""

import math
import random
from typing import Tuple

from geopy.distance import geodesic


def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two coordinates in meters.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in meters
    """
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def calculate_bearing(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate bearing (azimuth) from point 1 to point 2 in degrees.
    
    Args:
        lat1: Latitude of starting point
        lon1: Longitude of starting point
        lat2: Latitude of destination point
        lon2: Longitude of destination point
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = (
        math.cos(lat1_rad) * math.sin(lat2_rad)
        - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    )
    
    bearing = math.atan2(y, x)
    bearing_deg = math.degrees(bearing)
    return (bearing_deg + 360) % 360


def add_noise_to_coordinate(
    lat: float, lon: float, noise_meters: float
) -> Tuple[float, float]:
    """
    Add Gaussian noise to a coordinate.
    
    Args:
        lat: Original latitude
        lon: Original longitude
        noise_meters: Standard deviation of noise in meters
        
    Returns:
        Tuple of (noisy_lat, noisy_lon)
    """
    # Convert meters to approximate degrees (rough approximation)
    # 1 degree latitude ≈ 111,000 meters
    # 1 degree longitude ≈ 111,000 * cos(latitude) meters
    lat_noise_deg = random.gauss(0, noise_meters / 111000.0)
    lon_noise_deg = random.gauss(0, noise_meters / (111000.0 * math.cos(math.radians(lat))))
    
    return (lat + lat_noise_deg, lon + lon_noise_deg)


def calculate_destination(
    lat: float, lon: float, bearing: float, distance_meters: float
) -> Tuple[float, float]:
    """
    Calculate destination point given starting point, bearing, and distance.
    
    Args:
        lat: Starting latitude
        lon: Starting longitude
        bearing: Bearing in degrees (0-360)
        distance_meters: Distance to travel in meters
        
    Returns:
        Tuple of (destination_lat, destination_lon)
    """
    start = (lat, lon)
    destination = geodesic(meters=distance_meters).destination(start, bearing)
    return (destination.latitude, destination.longitude)


def is_within_range(
    lat1: float, lon1: float, lat2: float, lon2: float, max_range_meters: float
) -> bool:
    """
    Check if two points are within a specified range.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        max_range_meters: Maximum range in meters
        
    Returns:
        True if within range, False otherwise
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= max_range_meters

