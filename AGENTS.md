# AGENTS.md

## Project

`Agentic Game Builder MVP` is a Python CLI project that:

1. accepts a vague browser game idea
2. asks a few clarification questions
3. prints a structured game plan
4. generates `index.html`, `style.css`, and `game.js`
5. validates the output bundle

The main entrypoint is `python -m agentic_game_builder`.

## Requirements

- Python `3.11+`
- `uv`
- Docker, if you want to run the containerized flow

## Python Environment Setup

Always use a virtual environment for Python work in this repo.

Create the virtual environment with `uv`:

```bash
uv venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the project into the active virtual environment with `uv pip`:

```bash
uv pip install -e .
```

If new Python packages are ever added, install them with `uv pip install <package>` while the virtual environment is active, then record the dependency in `pyproject.toml`. Do not use plain `pip install` for this repo.

## Environment Variables

The app auto-loads a local `.env` file on startup.

Current default setup uses OpenRouter:

```bash
AIGB_PROVIDER=openai_compatible
AIGB_MODEL=qwen/qwen3-coder:free
AIGB_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

Required secret:

```bash
AIGB_API_KEY=...
```

Keep `.env` local only. It is gitignored and should not be committed.

## How To Run

Interactive mode:

```bash
python -m agentic_game_builder
```

Run with a prompt:

```bash
python -m agentic_game_builder --prompt "Make me a simple space survival game."
```

Write generated files into a specific directory:

```bash
python -m agentic_game_builder \
  --prompt "Create a jungle relic collection game." \
  --output-dir ./generated_games/jungle-demo
```

Use a JSON answers file for a scripted run:

```bash
python -m agentic_game_builder \
  --prompt "Make me a simple space survival game." \
  --answers-file ./answers.json \
  --output-dir ./generated_games/space-demo
```

## LLM Modes

Offline fallback mode:

```bash
export AIGB_PROVIDER=mock
```

OpenAI-compatible mode:

```bash
export AIGB_PROVIDER=openai_compatible
export AIGB_API_KEY=your_key_here
export AIGB_MODEL=gpt-4.1-mini
export AIGB_BASE_URL=https://api.openai.com/v1/chat/completions
```

## Build And Verification

Run tests:

```bash
python -m unittest discover -s tests -v
```

Run a syntax check:

```bash
python -m py_compile $(find agentic_game_builder tests -name '*.py')
```

Recommended local verification flow:

```bash
python -m unittest discover -s tests -v
python -m agentic_game_builder --prompt "Make me a simple space survival game."
```

## Docker

Build the image:

```bash
docker build -t agentic-game-builder .
```

Run interactively with a mounted output directory:

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --output-dir /app/generated_games/demo
```

Run with a prompt:

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a top-down zombie survival game." \
  --output-dir /app/generated_games/zombie-demo
```

## Important Files

- `agentic_game_builder/cli.py`: orchestrates the full CLI workflow
- `agentic_game_builder/clarification.py`: chooses clarification questions
- `agentic_game_builder/planner.py`: builds the bounded game spec
- `agentic_game_builder/generator.py`: generates the browser game files
- `agentic_game_builder/validator.py`: checks generated output
- `tests/test_pipeline.py`: basic end-to-end and unit coverage
- `README.md`: user-facing project overview and usage notes

## Notes

- Generated output is intentionally limited to small 2D canvas games.
- The current project has no third-party runtime dependencies, but setup should still go through `uv venv` and `uv pip install -e .`.
- Generated files are written to `generated_games/` by default unless `--output-dir` is provided.
