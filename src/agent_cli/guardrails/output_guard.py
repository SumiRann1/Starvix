from guardrails import Guard

from .validators import RedactSecretsValidator

output_guard = Guard().use(RedactSecretsValidator(on_fail="fix"))


def sanitize_output(text: str) -> str:
    """Scans and redacts any API keys or secrets before displaying or storing."""
    if not isinstance(text, str) or not text:
        return text

    try:
        result = output_guard.validate(text)
        return result.validated_output or text
    except Exception:  # noqa: BLE001
        return text
