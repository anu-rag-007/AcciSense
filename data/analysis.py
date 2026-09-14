def analyze_incident(severity_indicator: str):
    """
    Prototype incident analysis logic.

    This is intentionally rule-based for the first MVP.
    A trained ML model can replace this later.
    """

    severity = severity_indicator.lower()

    if severity in ["critical", "high"]:
        return {
            "severity": "CRITICAL",
            "priority": "P0"
        }

    elif severity == "medium":
        return {
            "severity": "MODERATE",
            "priority": "P1"
        }

    else:
        return {
            "severity": "LOW",
            "priority": "P2"
        }