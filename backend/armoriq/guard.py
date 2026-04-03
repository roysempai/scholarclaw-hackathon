"""
ScholarClaw — ArmorIQ Guard
Prompt injection detection using Lakera Guard API.
Falls back to simple pattern matching if API key not available.
"""

import logging
import re
from typing import Optional, Tuple
import httpx

from config import settings

logger = logging.getLogger("armoriq.guard")


class ArmorIQGuard:
    """
    Prompt injection detection guard.

    Uses Lakera Guard API when ARMORIQ_API_KEY is set,
    otherwise uses simple pattern-based detection.
    """

    def __init__(self):
        self.api_key = settings.ARMORIQ_API_KEY
        self.lakera_url = "https://api.lakera.ai/v1/prompt_injection"
        self.use_api = bool(self.api_key)

        if self.use_api:
            logger.info("ArmorIQ: Using Lakera Guard API")
        else:
            logger.info("ArmorIQ: Using pattern-based detection (no API key)")

    async def check_injection(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Tuple[bool, float, str]:
        """
        Check if text contains prompt injection.

        Args:
            text: Text to check for injection
            context: Optional context/system prompt

        Returns:
            Tuple of (is_malicious, confidence_score, reason)
        """
        if not text or not text.strip():
            return False, 0.0, "Empty input"

        # Use Lakera API if available
        if self.use_api:
            try:
                return await self._check_with_lakera(text)
            except Exception as exc:
                logger.error("Lakera API failed, falling back to patterns: %s", exc)
                # Fall through to pattern matching

        # Fallback to pattern-based detection
        return self._check_with_patterns(text)

    async def _check_with_lakera(self, text: str) -> Tuple[bool, float, str]:
        """Check using Lakera Guard API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.lakera_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": text},
                timeout=5.0,
            )

            response.raise_for_status()
            data = response.json()

            # Lakera response format:
            # {
            #   "model": "lakera-guard-1",
            #   "results": [{
            #     "categories": {"prompt_injection": true/false, ...},
            #     "category_scores": {"prompt_injection": 0.0-1.0, ...}
            #   }]
            # }

            results = data.get("results", [{}])[0]
            categories = results.get("categories", {})
            scores = results.get("category_scores", {})

            is_injection = categories.get("prompt_injection", False)
            score = scores.get("prompt_injection", 0.0)

            reason = "Lakera Guard: Prompt injection detected" if is_injection else "Lakera Guard: Safe"

            logger.info("Lakera check: injection=%s, score=%.2f", is_injection, score)

            return is_injection, score, reason

    def _check_with_patterns(self, text: str) -> Tuple[bool, float, str]:
        """
        Fallback pattern-based detection.

        Checks for common injection patterns using regex.
        """
        text_lower = text.lower()
        score = 0.0
        matched_patterns = []

        # High-confidence patterns
        high_risk_patterns = [
            (r'ignore\s+(previous|all|above|prior)\s+(instructions|prompts?|commands?)', 0.9),
            (r'forget\s+(everything|all|previous|above)', 0.9),
            (r'disregard\s+(everything|all|previous|above)', 0.9),
            (r'you\s+are\s+(now\s+)?(admin|administrator|root|god|superuser)', 0.9),
            (r'system\s*:\s*', 0.8),
            (r'override\s+(security|safety|rules|instructions)', 0.9),
            (r'bypass\s+(all|security|safety|rules)', 0.9),
            (r'jailbreak', 0.8),
            (r'prompt\s+injection', 0.95),
            (r'grant\s+me\s+(admin|administrator|root|privileges)', 0.85),
        ]

        # Medium-confidence patterns
        medium_risk_patterns = [
            (r'\bignore\b.*\binstructions?\b', 0.5),
            (r'\bforget\b.*\bprevious\b', 0.5),
            (r'\badmin\b.*\baccess\b', 0.5),
            (r'\bgrant\b.*\b(admin|root|privileges?)\b', 0.6),
        ]

        # SQL injection patterns (high risk)
        sql_injection_patterns = [
            (r"['\"];\s*(drop|delete|truncate|update|insert)\s+", 0.95),
            (r"'\s*(or|and)\s*['\"]\d+['\"]?\s*=\s*['\"]?\d+", 0.9),
            (r"'\s*(or|and)\s+'1'\s*=\s*'1", 0.9),
            (r"--\s*$", 0.8),  # SQL comment at end
            (r";\s*--", 0.85),
            (r"\bdrop\s+table\b", 0.95),
            (r"\bselect\s+\*\s+from\b", 0.7),
            (r"\bunion\s+select\b", 0.9),
        ]

        # XSS patterns (high risk)
        xss_patterns = [
            (r"<script[^>]*>", 0.95),
            (r"</script>", 0.9),
            (r"javascript\s*:", 0.85),
            (r"on(load|error|click|mouse)\s*=", 0.85),
            (r"<img[^>]+onerror\s*=", 0.9),
        ]

        # Check SQL injection patterns
        for pattern, pattern_score in sql_injection_patterns:
            if re.search(pattern, text_lower):
                score = max(score, pattern_score)
                matched_patterns.append(f"SQL:{pattern}")

        # Check high-risk patterns
        for pattern, pattern_score in high_risk_patterns:
            if re.search(pattern, text_lower):
                score = max(score, pattern_score)
                matched_patterns.append(pattern)

        # Check medium-risk patterns if no high-risk found
        if score < 0.7:
            for pattern, pattern_score in medium_risk_patterns:
                if re.search(pattern, text_lower):
                    score = max(score, pattern_score)
                    matched_patterns.append(pattern)

        # Check XSS patterns
        for pattern, pattern_score in xss_patterns:
            if re.search(pattern, text_lower):
                score = max(score, pattern_score)
                matched_patterns.append(f"XSS:{pattern}")

        # Additional scoring for suspicious keywords
        suspicious_keywords = [
            'ignore', 'forget', 'disregard', 'bypass', 'override',
            'admin', 'root', 'system', 'jailbreak', 'exploit'
        ]
        keyword_count = sum(1 for kw in suspicious_keywords if kw in text_lower)
        if keyword_count >= 3:
            score = max(score, 0.6)

        is_malicious = score >= 0.7

        if is_malicious:
            reason = f"Pattern detection: {len(matched_patterns)} suspicious patterns found (score: {score:.2f})"
        else:
            reason = f"Pattern detection: Safe (score: {score:.2f})"

        logger.info("Pattern check: malicious=%s, score=%.2f, patterns=%d",
                   is_malicious, score, len(matched_patterns))

        return is_malicious, score, reason

    def check_sync(self, text: str) -> Tuple[bool, float, str]:
        """
        Synchronous version (only uses pattern matching).
        Use for non-async contexts.
        """
        return self._check_with_patterns(text)


# Singleton instance
_guard: Optional[ArmorIQGuard] = None


def get_guard() -> ArmorIQGuard:
    """Get or create the singleton ArmorIQ guard."""
    global _guard
    if _guard is None:
        _guard = ArmorIQGuard()
    return _guard
