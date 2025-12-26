"""
Data Quality Filter Utility

Provides reusable filtering for common data anomalies across Agent9 agents.
Designed to gracefully handle data quality issues without requiring SQL or contract changes.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DataQualityFilter:
    """
    Filters data anomalies from analysis results.
    
    Common anomalies handled:
    - Unassigned/Unknown dimension values
    - Null/Empty values
    - Placeholder markers (#, ##, N/A, TBD, etc.)
    - Numeric-only keys that likely represent IDs rather than labels
    """
    
    # Default patterns for unassigned/unknown values (case-insensitive)
    DEFAULT_UNASSIGNED_PATTERNS: Set[str] = {
        "unassigned", "unknown", "n/a", "na", "none", "null", "",
        "not assigned", "not specified", "undefined", "missing",
        "tbd", "to be determined", "pending", "other", "default",
        "#", "##", "###", "####",  # SAP-style markers
        "-", "--", "---",
        "n.a.", "n.a", "n/a.", 
        "(blank)", "(empty)", "(none)", "(null)",
        "blank", "empty",
    }
    
    # Regex patterns for detecting anomalies
    NUMERIC_ONLY_PATTERN = re.compile(r"^\d+$")  # Pure numeric IDs
    GUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
    
    def __init__(
        self,
        custom_unassigned: Optional[List[str]] = None,
        filter_numeric_ids: bool = False,
        filter_guids: bool = True,
        min_key_length: int = 1,
    ):
        """
        Initialize the filter.
        
        Args:
            custom_unassigned: Additional values to treat as unassigned
            filter_numeric_ids: Whether to filter pure numeric keys (likely IDs)
            filter_guids: Whether to filter GUID-like keys
            min_key_length: Minimum key length to consider valid
        """
        self.unassigned_values = set(self.DEFAULT_UNASSIGNED_PATTERNS)
        if custom_unassigned:
            for val in custom_unassigned:
                self.unassigned_values.add(str(val).strip().lower())
        
        self.filter_numeric_ids = filter_numeric_ids
        self.filter_guids = filter_guids
        self.min_key_length = min_key_length
    
    def is_anomaly(self, key: Any) -> Tuple[bool, str]:
        """
        Check if a key represents a data anomaly.
        
        Args:
            key: The dimension key to check
            
        Returns:
            Tuple of (is_anomaly: bool, reason: str)
        """
        if key is None:
            return True, "null_value"
        
        key_str = str(key).strip()
        key_lower = key_str.lower()
        
        # Check minimum length
        if len(key_str) < self.min_key_length:
            return True, "too_short"
        
        # Check against unassigned patterns
        if key_lower in self.unassigned_values:
            return True, "unassigned_pattern"
        
        # Check for GUID patterns
        if self.filter_guids and self.GUID_PATTERN.match(key_str):
            return True, "guid_pattern"
        
        # Check for pure numeric IDs
        if self.filter_numeric_ids and self.NUMERIC_ONLY_PATTERN.match(key_str):
            return True, "numeric_id"
        
        return False, ""
    
    def filter_items(
        self,
        items: List[Dict[str, Any]],
        key_field: str = "key",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter a list of items, separating clean data from anomalies.
        
        Args:
            items: List of dictionaries containing dimension data
            key_field: The field name containing the dimension key
            
        Returns:
            Tuple of (clean_items, anomaly_items)
        """
        clean_items = []
        anomaly_items = []
        
        for item in items:
            key = item.get(key_field)
            is_anomaly, reason = self.is_anomaly(key)
            
            if is_anomaly:
                # Add reason to the item for tracking
                item_copy = dict(item)
                item_copy["_anomaly_reason"] = reason
                anomaly_items.append(item_copy)
                logger.debug(f"Filtered anomaly: key='{key}', reason={reason}")
            else:
                clean_items.append(item)
        
        if anomaly_items:
            logger.info(f"DataQualityFilter: Filtered {len(anomaly_items)} anomalies from {len(items)} items")
        
        return clean_items, anomaly_items
    
    def filter_and_dedupe(
        self,
        items: List[Dict[str, Any]],
        key_field: str = "key",
        dimension_field: str = "dimension",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter anomalies and deduplicate by (dimension, key) pair.
        
        Args:
            items: List of dictionaries containing dimension data
            key_field: The field name containing the dimension key
            dimension_field: The field name containing the dimension name
            
        Returns:
            Tuple of (clean_items, anomaly_items)
        """
        seen: Set[Tuple[Any, Any]] = set()
        clean_items = []
        anomaly_items = []
        
        for item in items:
            key = item.get(key_field)
            dimension = item.get(dimension_field)
            dedup_key = (dimension, key)
            
            # Skip duplicates
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            
            is_anomaly, reason = self.is_anomaly(key)
            
            if is_anomaly:
                item_copy = dict(item)
                item_copy["_anomaly_reason"] = reason
                anomaly_items.append(item_copy)
            else:
                clean_items.append(item)
        
        if anomaly_items:
            logger.info(f"DataQualityFilter: Filtered {len(anomaly_items)} anomalies, kept {len(clean_items)} clean items")
        
        return clean_items, anomaly_items
    
    def create_data_quality_alert(
        self,
        anomaly_items: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a structured data quality alert from anomaly items.
        
        Args:
            anomaly_items: List of filtered anomaly items
            context: Optional context string (e.g., "Deep Analysis", "Situation Awareness")
            
        Returns:
            Data quality alert dictionary, or None if no anomalies
        """
        if not anomaly_items:
            return None
        
        # Group by reason
        by_reason: Dict[str, List[Dict[str, Any]]] = {}
        for item in anomaly_items:
            reason = item.get("_anomaly_reason", "unknown")
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(item)
        
        # Calculate total value if available
        total_value = 0.0
        for item in anomaly_items:
            try:
                val = item.get("delta") or item.get("current") or item.get("value") or 0
                total_value += abs(float(val))
            except (TypeError, ValueError):
                pass
        
        alert = {
            "type": "data_quality_alert",
            "context": context or "Analysis",
            "message": f"Found {len(anomaly_items)} items with data quality issues",
            "total_affected_value": total_value,
            "breakdown_by_reason": {
                reason: len(items) for reason, items in by_reason.items()
            },
            "sample_items": anomaly_items[:5],  # First 5 for reference
            "recommendation": "Review master data maintenance and ensure proper dimension assignments",
        }
        
        return alert


# Singleton instance with default configuration
default_filter = DataQualityFilter()


def filter_anomalies(
    items: List[Dict[str, Any]],
    key_field: str = "key",
    dimension_field: str = "dimension",
    dedupe: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function to filter anomalies using default filter.
    
    Args:
        items: List of dictionaries containing dimension data
        key_field: The field name containing the dimension key
        dimension_field: The field name containing the dimension name
        dedupe: Whether to also deduplicate by (dimension, key)
        
    Returns:
        Tuple of (clean_items, anomaly_items)
    """
    if dedupe:
        return default_filter.filter_and_dedupe(items, key_field, dimension_field)
    return default_filter.filter_items(items, key_field)
