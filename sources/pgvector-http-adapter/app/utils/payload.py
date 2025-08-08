"""
Utility functions for payload processing
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def parse_payload(payload: Any) -> Dict[str, Any]:
    """
    Parse payload to ensure it's a dictionary.
    Handles both string (JSON) and dict inputs.

    Args:
        payload: Input payload (string or dict)

    Returns:
        Dict representation of payload
    """
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse payload JSON: {e}")
            return {}
    elif isinstance(payload, dict):
        return payload
    else:
        logger.warning(f"Unexpected payload type: {type(payload)}")
        return {}
