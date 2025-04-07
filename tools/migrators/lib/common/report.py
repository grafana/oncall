TAB = " " * 4
SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"
WARNING_SIGN = "⚠️"  # TODO: warning sign does not renders properly


def format_error_list(errors: list[str]) -> str:
    """Format a list of errors into a string with bullet points."""
    if not errors:
        return ""
    return "\n".join(f"{TAB}- {error}" for error in errors)
