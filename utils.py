import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

def resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource."""
    try:
        base_path = Path(__file__).parent.absolute()
        return str(base_path / relative_path)
    except Exception as e:
        logging.error(f"Error getting resource path for {relative_path}: {e}")
        return relative_path

def load_json_schema(schema_path: str) -> Optional[Dict]:
    """Load a JSON schema file."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON schema from {schema_path}: {e}")
        return None

def validate_json_schema(data: Any, schema: Dict) -> bool:
    """Validate data against a JSON schema."""
    try:
        # Simple validation - in a real app, use jsonschema library
        if not isinstance(data, type(schema)):
            return False
        return True
    except Exception as e:
        logging.error(f"Error validating JSON schema: {e}")
        return False

def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely load JSON data from a file."""
    try:
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        if not file_path.exists():
            logging.warning(f"File not found: {file_path}")
            return default
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        return default
    except Exception as e:
        logging.error(f"Error loading JSON from {file_path}: {e}")
        return default
