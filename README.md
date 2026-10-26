# Starvix (`starvix-agent-runtime`)

An advanced, developer-first AI chatbot and agent CLI runtime built with LangGraph, LangChain, and Rich.

```text
  ███████╗████████╗ █████╗ ██████╗ ██╗   ██╗██╗██╗  ██╗
  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║   ██║██║╚██╗██╔╝
  ███████╗   ██║   ███████║██████╔╝██║   ██║██║ ╚███╔╝ 
  ╚════██║   ██║   ██╔══██║██╔══██╗╚██╗ ██╔╝██║ ██╔██╗ 
  ███████║   ██║   ██║  ██║██║  ██║ ╚████╔╝ ██║██╔╝ ██╗
  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝
```

## Features

- **Modern TUI**: Designer themes (`tokyo_night`, `catppuccin`, `dracula`, `nord`, `cyberpunk`, `matrix`, etc.), framed message cards, live syntax-highlighted streaming, `<think>` reasoning foldout, collapsible tool execution trees, and telemetry badges.
- **Multi-Provider Support**: Seamlessly switch between Groq, Google Gemini, and OpenRouter models with `/switch <model>`.
- **Long-Term Memory (LTM)**: Store, search, and recall cross-session memories with SQLite vector & keyword checkpointers.
- **Developer Tools**: Direct bash execution (`!command`), `@file` context injection, Human-In-The-Loop approval cards, and `/export` / `/copy`.
- **Config-Driven**: Configure themes, models, temperature, and API keys via `config.yaml` and `.env`.

## Installation

Install in editable mode:

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

2. Launch Starvix:
   ```bash
   starvix chat
   ```

3. Explore commands:
   - `/theme` - View themes and switch color palettes dynamically with color swatches
   - `/models` - View and switch active AI models
   - `/threads` - Manage conversation threads
   - `/clear` - Clear terminal screen
   - `/help` - Open categorized command guide

