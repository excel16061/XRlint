"""XRLint: a static checker for risky UI properties in A-Frame / WebXR pages."""

__version__ = "0.1.0"
__author__ = "Syed Omer Ali"
__maintainer__ = "Syed Omer Ali"
__email__ = "omer@exetech.dev"

from .analyzer import analyze_paths, analyze_html  # noqa: E402,F401
from .model import RULES, Finding, Severity  # noqa: E402,F401
