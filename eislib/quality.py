def assign_quality(warnings_list):
    """Assign quality tier based on warning list."""
    if any("UNUSABLE" in w or "CRITICAL" in w for w in warnings_list):
        return "DO NOT USE"
    if any("Excessive" in w or "cable-dominated" in w for w in warnings_list):
        return "POOR"
    if not warnings_list:
        return "OK"
    return "WARN"
