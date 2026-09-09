"""Metrics loading and parameter parsing utilities."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MetricsLoader:
    """Loads metrics from JSON files or dicts and parses CLI key=value parameters."""

    @staticmethod
    def from_json_file(path: str) -> Dict[str, float]:
        """Load numerical metrics from a JSON file.

        Returns empty dict on missing or malformed JSON file with a warning logged.
        """
        if not path or not os.path.exists(path):
            logger.warning("Metrics file not found: %s", path)
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to decode metrics JSON from %s: %s", path, exc)
            return {}

        if not isinstance(data, dict):
            logger.warning("Metrics JSON root must be an object: %s", path)
            return {}

        return MetricsLoader.from_dict(data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dict[str, float]:
        """Extract all numeric metric values from a dictionary."""
        metrics: Dict[str, float] = {}
        for k, v in data.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                metrics[str(k)] = float(v)
            elif isinstance(v, str):
                try:
                    metrics[str(k)] = float(v)
                except ValueError:
                    continue
        return metrics

    @staticmethod
    def parse_cli_params(params: List[str]) -> Dict[str, Any]:
        """Parse list of CLI key=value parameter strings into typed dictionary."""
        import re

        result: Dict[str, Any] = {}
        tokens: List[str] = []
        for item in params:
            if not item:
                continue
            # Split tokens on spaces and commas while preserving key=value
            parts = re.split(r"[\s,]+", item.strip())
            tokens.extend([p for p in parts if p])

        for item in tokens:
            if "=" not in item:
                continue
            key, val = item.split("=", 1)
            key = key.strip()
            val = val.strip().strip(",")

            if not key:
                continue

            # Try integer
            try:
                result[key] = int(val)
                continue
            except ValueError:
                pass

            # Try float
            try:
                result[key] = float(val)
                continue
            except ValueError:
                pass

            # Try boolean
            if val.lower() in ("true", "yes", "1"):
                result[key] = True
            elif val.lower() in ("false", "no", "0"):
                result[key] = False
            else:
                result[key] = val

        return result
