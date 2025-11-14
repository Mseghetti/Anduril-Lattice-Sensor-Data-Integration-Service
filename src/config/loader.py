"""Configuration file loading and validation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if config is None:
        return {}
    
    return config


def load_sensor_config(config_path: str) -> Dict[str, Any]:
    """
    Load a sensor configuration file.
    
    Args:
        config_path: Path to the sensor config file
        
    Returns:
        Sensor configuration dictionary
        
    Raises:
        ValueError: If config is invalid
    """
    config = load_config(config_path)
    
    # Validate required fields
    required_fields = ["sensor_type", "sensor_id", "position"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in sensor config: {field}")
    
    return config


def load_scenario_config(config_path: str) -> Dict[str, Any]:
    """
    Load a scenario configuration file.
    
    Args:
        config_path: Path to the scenario config file
        
    Returns:
        Scenario configuration dictionary
        
    Raises:
        ValueError: If config is invalid
    """
    config = load_config(config_path)
    
    # Validate required fields
    if "sensors" not in config:
        raise ValueError("Missing required field in scenario config: sensors")
    
    if "entities" not in config:
        raise ValueError("Missing required field in scenario config: entities")
    
    return config


def validate_config(config: Dict[str, Any], config_type: str = "sensor") -> List[str]:
    """
    Validate a configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        config_type: Type of config ("sensor" or "scenario")
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors: List[str] = []
    
    if config_type == "sensor":
        required_fields = ["sensor_type", "sensor_id", "position"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        if "position" in config:
            pos = config["position"]
            if not isinstance(pos, dict):
                errors.append("Position must be a dictionary")
            else:
                if "lat" not in pos or "lon" not in pos:
                    errors.append("Position must contain 'lat' and 'lon'")
                else:
                    if not (-90 <= pos["lat"] <= 90):
                        errors.append("Latitude must be between -90 and 90")
                    if not (-180 <= pos["lon"] <= 180):
                        errors.append("Longitude must be between -180 and 180")
        
        if "update_rate_hz" in config:
            rate = config["update_rate_hz"]
            if not isinstance(rate, (int, float)) or rate <= 0:
                errors.append("update_rate_hz must be a positive number")
    
    elif config_type == "scenario":
        if "sensors" not in config:
            errors.append("Missing required field: sensors")
        elif not isinstance(config["sensors"], list):
            errors.append("sensors must be a list")
        
        if "entities" not in config:
            errors.append("Missing required field: entities")
        elif not isinstance(config["entities"], list):
            errors.append("entities must be a list")
    
    return errors


def find_config_file(filename: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Find a config file in common locations.
    
    Args:
        filename: Name of the config file
        search_dirs: Optional list of directories to search
        
    Returns:
        Path to the config file if found, None otherwise
    """
    if search_dirs is None:
        # Default search directories
        project_root = Path(__file__).parent.parent.parent
        search_dirs = [
            str(project_root / "config"),
            str(project_root / "config" / "sensors"),
            str(project_root / "config" / "scenarios"),
            str(project_root),
        ]
    
    for search_dir in search_dirs:
        path = Path(search_dir) / filename
        if path.exists():
            return str(path)
    
    return None

