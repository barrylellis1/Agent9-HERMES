async def _map_business_processes_to_strings(self, business_processes: List[Any]) -> List[str]:
    """Convert business process objects to string values.
    
    Args:
        business_processes: List of business process objects or strings
        
    Returns:
        List of business process strings
    """
    result = []
    
    for bp in business_processes:
        if isinstance(bp, str):
            # Already a string, use directly
            result.append(bp)
        elif hasattr(bp, 'display_name') and bp.display_name:
            # Business process object with display_name
            result.append(bp.display_name)
        elif hasattr(bp, 'name') and bp.name:
            # Business process object with name
            result.append(bp.name)
        else:
            # Try to convert to string
            try:
                result.append(str(bp))
            except Exception as e:
                self.logger.warning(f"Could not convert business process to string: {e}")
    
    # Filter out None values
    return [bp for bp in result if bp is not None]
