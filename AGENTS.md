# AGENTS.md

## Project

`Agentic Game Builder MVP` is a Python CLI project that:

1. accepts a vague browser game idea
2. asks targeted clarification and personalization questions
3. decides the runtime framework (`vanilla_js` or `phaser`)
4. prints a structured game plan
5. generates `index.html`, `style.css`, and `game.js`
6. validates the output bundle

The main entrypoint is `python -m agentic_game_builder`.

## Requirements

- Python `3.11+`
- `uv`
- Docker, if you want to run the containerized flow

## Python Environment Setup

Always use a virtual environment for Python work in this repo.

Recommended shell note:

- in WSL/Linux, prefer `python3` to create the virtual environment
- after activation, use `python`
- if `python` points to a broken Windows shim, use `.venv/bin/python` directly

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

If `uv` is not installed yet:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

Quick environment bootstrap sequence:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Environment Variables

The app auto-loads a local `.env` file on startup.

Current default setup uses role-based LLM routing:

```bash
AIGB_GROQ_PRIMARY_MODEL=openai/gpt-oss-120b
AIGB_GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
AIGB_OPENROUTER_MODEL=qwen/qwen3-coder:free
AIGB_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

Required secret:

```bash
AIGB_GROQ_API_KEY=...
AIGB_OPENROUTER_API_KEY=...
```

Keep `.env` local only. It is gitignored and should not be committed.

## How To Run

Default workflow phases printed by the CLI:

1. Clarify
2. Select Framework
3. Plan
4. Generate
5. Validate

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

Force mock mode for offline or rate-limit-safe testing:

```bash
AIGB_PROVIDER=mock python -m agentic_game_builder --prompt "Make me a simple space survival game."
```

Run using the venv Python directly without activation:

```bash
.venv/bin/python -m agentic_game_builder --prompt "Make me a simple space survival game."
```

Typical answer file shape:

```json
{
  "objective": "Collect data caches while dodging security drones.",
  "player_identity": "freelance courier",
  "perspective": "top-down",
  "controls": "WASD",
  "lose_condition": "Lose if security drones trap the player.",
  "signature_mechanic": "Use a short dash burst to steal data caches.",
  "progression_style": "faster waves",
  "visual_tone": "mysterious",
  "arena_detail": "a neon archive vault"
}
```

## LLM Modes

Offline fallback mode:

```bash
export AIGB_PROVIDER=mock
```

Optional role overrides:

```bash
export AIGB_DESIGN_PROVIDER=openai_compatible
export AIGB_DESIGN_API_KEY=your_key_here
export AIGB_DESIGN_MODEL=openai/gpt-oss-120b
export AIGB_DESIGN_BASE_URL=https://api.groq.com/openai/v1/chat/completions

export AIGB_CODEGEN_PROVIDER=openai_compatible
export AIGB_CODEGEN_API_KEY=your_key_here
export AIGB_CODEGEN_MODEL=qwen/qwen3-coder:free
export AIGB_CODEGEN_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

## Build And Verification

Run the full test suite:

```bash
python -m unittest discover -s tests -v
```

Run one specific test module:

```bash
python -m unittest tests.test_pipeline -v
```

Run a syntax check:

```bash
python -m py_compile $(find agentic_game_builder tests -name '*.py')
```

Inspect the currently resolved provider config:

```bash
python -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(type(clients.clarification_client).__name__); print(type(clients.code_generation_client).__name__); print(*clients.notes, sep='\n')"
```

Recommended local smoke test:

```bash
AIGB_PROVIDER=mock python -m agentic_game_builder \
  --prompt "Make a traffic dodging game where the player crosses busy lanes." \
  --output-dir ./generated_games/smoke-test
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

Run Docker in mock mode to avoid live API dependencies:

```bash
docker run --rm -it \
  --env AIGB_PROVIDER=mock \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a simple space survival game." \
  --output-dir /app/generated_games/mock-demo
```

## Important Files

- `agentic_game_builder/cli.py`: orchestrates the full CLI workflow
- `agentic_game_builder/clarification.py`: chooses clarification questions
- `agentic_game_builder/framework_selector.py`: framework-selection phase
- `agentic_game_builder/planner.py`: builds the bounded game spec
- `agentic_game_builder/generator.py`: generates the browser game files
- `agentic_game_builder/validator.py`: checks generated output
- `tests/test_pipeline.py`: basic end-to-end and unit coverage
- `project_update.md`: running implementation log and change history
- `README.md`: user-facing project overview and usage notes

## Operator Notes

- Generated output is intentionally limited to small 2D canvas games.
- Clarification can ask about player identity, signature mechanic, pacing, tone, and arena details to reduce repetitive output.
- Framework selection is an explicit phase and can choose either `vanilla_js` or `phaser`.
- The current project has no third-party runtime dependencies, but setup should still go through `uv venv` and `uv pip install -e .`.
- Generated files are written to `generated_games/` by default unless `--output-dir` is provided.
- After each feature, fix, or meaningful change, commit the work and push it to the git repository.
- If live providers fail or rate-limit, the CLI can still fall back to deterministic mock behavior.
- If an `--answers-file` does not cover every required clarification answer, the CLI exits with a clear message instead of hanging.
- Extra `--answers-file` keys are still passed into planning even if the capped question list did not explicitly prompt for them.
- Phaser output loads Phaser from a CDN in `index.html`; vanilla output does not.
- If Docker is unavailable in WSL, enable Docker Desktop WSL integration or run the local Python flow instead.
