# ChatBot CLI (`agent-cli`)

A modular multi-provider AI chatbot and agent CLI application built with LangChain and Pydantic.

## Features

- **Multi-Provider Support**: Seamlessly switch between Groq, Google Gemini, and OpenRouter models.
- **Config-Driven**: Configure default models, temperature, and API keys via `config.yaml` and `.env`.
- **Extensible Architecture**: Clean separation between configuration, model initialization, and agent logic.

## Installation

Install the package in editable mode:

```bash
pip install -e .
```

Or using `uv`:

```bash
uv pip install -e .
```

## Quick Start

1. Set up your API keys in `.env`:
   ```bash
   GROQ_API_KEY=your_key_here
   OPENROUTER_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

2. Configure models in `config.yaml`.

3. Test models:
   ```bash
   python scripts/try_models.py
   ```
