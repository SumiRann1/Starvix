from guardrails import Guard
from guardrails.errors import ValidationError

from .validators import DetectEmotionsValidator, PromptInjectionValidator

prompt_injection_guard = Guard().use(PromptInjectionValidator(on_fail="exception"))
emotion_guard = Guard().use(DetectEmotionsValidator(on_fail="exception"))


def check_input(user_input: str) -> str:
    """Validates user input to detect prompt injection or jailbreak attempts.

    Raises:
        ValidationError: If prompt injection patterns are detected.
    """
    if not isinstance(user_input, str):
        return user_input

    prompt_injection_guard.validate(user_input)
    return user_input


def validate_emotion(user_input: str) -> str:
    """Validate user input to detect any emotions.

    Raises:
        ValidationError: If emotional patterns are detected.
    """
    if not isinstance(user_input, str):
        return user_input

    emotion_guard.validate(user_input)
    return user_input

