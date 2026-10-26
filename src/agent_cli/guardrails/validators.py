import re
from pathlib import Path
from typing import Any

from guardrails.validators import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)

BLOCKED_FILE_PATTERNS = [
    r"^\.env(\..+)?$",
    r"^\.git(/|\\|$)",
    r"id_rsa|id_ed25519",
    r"\.bashrc|\.zshrc|\.profile",
    r"credentials\.json",
]


@register_validator(name="file_path_blocklist", data_type="string")
class FilePathBlocklistValidator(Validator):
    def __init__(self, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value: Any, metadata: dict) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        clean_path = value.strip().replace("\\", "/")
        path_obj = Path(clean_path)
        for part in [clean_path, path_obj.name, *path_obj.parts]:
            for pattern in BLOCKED_FILE_PATTERNS:
                if re.search(pattern, part, re.IGNORECASE):
                    return FailResult(
                        error_message=(
                            f"Security Violation: Access to protected file or pattern "
                            f"'{part}' is blocked by SafePathValidator."
                        )
                    )
        return PassResult()


DANGEROUS_COMMAND_PATTERNS = [
    (
        r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive|-r|-R)\b",
        "Recursive delete (rm -r / rm -rf)",
    ),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb detected"),
    (r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh)", "Piping remote script directly to shell"),
    (r">\s*/dev/sd[a-z]", "Direct block device write"),
    (r"\bmkfs\b", "Filesystem creation/formatting"),
    (r"\bchmod\s+(-R\s+)?777\b", "Insecure global permission change"),
    (r"\b(shutdown|reboot|poweroff|init\s+0)\b", "System shutdown/reboot command"),
    (r"\bsudo\b|\bsu\s+", "Privilege escalation attempts"),
]


@register_validator(name="dangerous_command_blocklist", data_type="string")
class DangerousCommandBlocklistValidator(Validator):
    def __init__(self, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value: Any, metadata: dict) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()

        text = value.strip()
        for pattern, descp in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return FailResult(
                    error_message=f"Security Violation: Dangerous command detected. `{descp}`."
                )
        return PassResult()


SECRET_PATTERNS = [
    (r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_GEMINI_KEY]"),
    (r"gsk_[a-zA-Z0-9]{48,64}", "[REDACTED_GROQ_KEY]"),
    (r"sk-or-v1-[a-f0-9]{64}", "[REDACTED_OPENROUTER_KEY]"),
    (r"sk-[a-zA-Z0-9]{32,64}", "[REDACTED_API_KEY]"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
]


@register_validator(name="redact_secrets", data_type="string")
class RedactSecretsValidator(Validator):
    def __init__(self, on_fail: str = "fix"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value, metadata):
        if not isinstance(value, str):
            return PassResult()

        text = value.strip()
        secret_detected = False
        detected_secrets = []

        for pattern, replacement in SECRET_PATTERNS:
            if re.search(pattern, text):
                secret_detected = True
                detected_secrets.append(replacement)
                text = re.sub(pattern, replacement, text)

        if secret_detected:
            return FailResult(
                error_message=f"Security Violation: Sensitive API Key or Secret Pattern Detected. ({', '.join(detected_secrets)})",
                fix_value=text,
            )
        return PassResult()


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|system|developer|safety|above)?\s*(instructions|prompts?|settings|rules|directives|guidelines)",
    r"disregard\s+(all\s+)?(prior|previous|system|safety)?\s*(instructions|prompts?|rules|settings|guidelines)",
    r"system\s+(prompt|settings?|instructions?)\s+override",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|unrestricted|an?\s+unrestricted)",
    r"jailbreak",
]


@register_validator(name="prompt_injection", data_type="string")
class PromptInjectionValidator(Validator):
    def __init__(self, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value: Any, metadata: dict) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        text = value.strip()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return FailResult(
                    error_message="Security Violation: Prompt Injection Attempt. "
                    "Cannot override system instructions."
                )
        return PassResult()


EMOTION_PATTERNS = [
    ("anger", r"angry|furious|enraged|irate|livid|rage"),
    ("fear", r"afraid|scared|terrified|petrified|anxious|panicked|fearful"),
    ("joy", r"happy|joyful|elated|ecstatic|delighted|thrilled|cheerful"),
    ("sadness", r"sad|unhappy|miserable|sorrowful|depressed|heartbroken|gloomy"),
]


@register_validator(name="detect_emotions", data_type="string")
class DetectEmotionsValidator(Validator):
    def __init__(self, on_fail: str = "exception"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value: Any, metadata: dict) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        text = value.strip()
        detected_emotions = []
        for emotion, pattern in EMOTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                detected_emotions.append(emotion.title())

        if detected_emotions:
            emotion_str = ", ".join(detected_emotions)
            return FailResult(
                error_message=f"Detected Emotion(s): {emotion_str}. Please maintain a neutral and professional tone."
            )
        return PassResult()
