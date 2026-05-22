"""
PII Redaction engine.

Detects and redacts personally identifiable information from
log payloads before they are published to the event bus.
"""

import re
from typing import Optional

from backend.config import settings


class PIIRedactor:
    """Regex-based PII detection and redaction."""

    # Compiled regex patterns for PII detection
    PATTERNS = {
        "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
        "PHONE": re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    }

    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = enabled if enabled is not None else settings.pii_redaction_enabled

    def redact(self, text: str) -> str:
        """
        Redact PII from the given text.

        Args:
            text: Input text that may contain PII.

        Returns:
            Text with PII replaced by [REDACTED_<TYPE>] tokens.
        """
        if not self.enabled or not text:
            return text

        result = text
        for pii_type, pattern in self.PATTERNS.items():
            result = pattern.sub(f"[REDACTED_{pii_type}]", result)

        return result
