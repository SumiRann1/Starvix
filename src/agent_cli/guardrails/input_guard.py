from guardrails import Guard
from guardrails.errors import ValidationError

from .validators import DetectEmotionsValidator, PromptInjectionValidator

prompt_injection_guard = Guard().use(PromptInjectionValidator(on_fail="exception"))
emotion_guard = Guard().use(DetectEmotionsValidator(on_fail="exception"))


def check_input(user_input: str):
    """Validates user input to detect prompt injection or jailbreak attempts.

    Raises:
        ValidationError: If prompt injection patterns are detected.
    """

    if not isinstance(user_input, str):
        return user_input
    try:
        result = prompt_injection_guard.validate(user_input)
        return result.validated_output or user_input
    except ValidationError:
        raise ValueError("Prompt Injection Attempt")


def validate_emotion(user_input: str):
    """Validate user input to detect any emotions."""
    if not isinstance(user_input, str):
        return user_input
    try:
        result = emotion_guard.validate(user_input)
        return result.validated_output or user_input
    except ValidationError:
        raise ValueError("Emotion Detected")
