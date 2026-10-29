"""JP Zengin Name: format, check and compare Japanese bank-transfer account names (振込名義カナ)."""
from .name import check_name, format_name, match_key, match_names, to_halfwidth

__version__ = "0.1.0"
__all__ = ["format_name", "check_name", "match_names", "match_key", "to_halfwidth", "__version__"]
