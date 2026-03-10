# Agentic Game Builder MVP

`Agentic Game Builder MVP` is a Python CLI agent that takes a vague browser-game idea, asks clarification questions, builds a structured implementation plan, generates a playable browser game bundle, and validates the output.

The workflow is intentionally explicit:

1. Clarify
2. Select Framework
3. Plan
4. Generate
5. Validate

The project is intentionally scoped to small 2D browser games so the output stays inspectable, debuggable, and realistic for assignment-style review.

## What The Agent Produces

Each successful run writes a local game bundle containing:

- `index.html`
- `style.css`
- `game.js`

By default, generated bundles are written under `generated_games/`, unless `--output-dir` is provided.

## Prerequisites

- Python `3.11+`
- `uv`
- Docker if you want to test the containerized workflow

## How To Run The Agent

### Shared setup for all operating systems

Before you run any OS-specific commands below, create a local `.env` file in the repo root.

Typical live setup:

```bash
AIGB_GROQ_API_KEY=your_groq_key_here
AIGB_GROQ_PRIMARY_MODEL=openai/gpt-oss-120b
AIGB_GROQ_CODEGEN_FALLBACK_MODEL=moonshotai/kimi-k2-instruct-0905
AIGB_GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions

AIGB_OPENROUTER_API_KEY=your_openrouter_key_here
AIGB_OPENROUTER_MODEL=qwen/qwen3-coder:free
AIGB_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

Keep `.env` local only. It is gitignored and should not be committed.

The app auto-loads `.env` automatically at startup, so you usually do not need to export variables manually in your shell.

Expected default live behavior:

- clarification and planning use Groq `openai/gpt-oss-120b`
- code generation tries OpenRouter `qwen/qwen3-coder:free`
- if OpenRouter fails or rate-limits, code generation falls back to Groq `moonshotai/kimi-k2-instruct-0905`

Example `answers.json` for scripted runs:

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

### Linux / WSL

#### 1. Open the repo

```bash
cd /path/to/AI-Game-builder
```

Example in WSL:

```bash
cd /mnt/c/Users/Admin/Documents/AI-Game-builder
```

#### 2. Create the virtual environment

```bash
uv venv .venv
```

#### 3. Activate the environment

```bash
source .venv/bin/activate
```

#### 4. Install the project into the environment

```bash
uv pip install -e .
```

If you do not want to activate the environment, use `.venv/bin/python` directly in all commands below.

#### 5. Verify the resolved model routing

```bash
.venv/bin/python -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

#### 6. Run interactively

```bash
.venv/bin/python -m agentic_game_builder
```

The CLI will:

- ask for the initial game idea if `--prompt` is not provided
- ask clarification questions when the prompt is still ambiguous
- print the structured plan before generation
- generate and validate the game bundle

#### 7. Run with a direct prompt

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Make a cyber heist game about stealing data from a neon vault."
```

#### 8. Run with a fixed output directory

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Create a jungle relic collection game." \
  --output-dir ./generated_games/jungle-demo
```

#### 9. Run with an answers file

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Make a cyber heist game about stealing data." \
  --answers-file ./answers.json \
  --output-dir ./generated_games/heist-scripted
```

#### 10. Run in offline mock mode

```bash
AIGB_PROVIDER=mock .venv/bin/python -m agentic_game_builder \
  --prompt "Make a traffic dodging game where the player crosses busy lanes." \
  --output-dir ./generated_games/mock-smoke
```

In mock mode:

- clarification falls back to local heuristics
- planning still produces deterministic plan copy
- code generation falls back to the built-in template runtime

#### 11. Open the generated game

```bash
xdg-open generated_games/mock-smoke/index.html
```

### macOS

#### 1. Open the repo

```bash
cd /path/to/AI-Game-builder
```

#### 2. Create the virtual environment

```bash
uv venv .venv
```

#### 3. Activate the environment

```bash
source .venv/bin/activate
```

#### 4. Install the project into the environment

```bash
uv pip install -e .
```

If your shell does not resolve `python` cleanly after activation, use `.venv/bin/python` directly.

#### 5. Verify the resolved model routing

```bash
.venv/bin/python -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

#### 6. Run interactively

```bash
.venv/bin/python -m agentic_game_builder
```

#### 7. Run with a direct prompt

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Make a cyber heist game about stealing data from a neon vault."
```

#### 8. Run with a fixed output directory

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Create a jungle relic collection game." \
  --output-dir ./generated_games/jungle-demo
```

#### 9. Run with an answers file

```bash
.venv/bin/python -m agentic_game_builder \
  --prompt "Make a cyber heist game about stealing data." \
  --answers-file ./answers.json \
  --output-dir ./generated_games/heist-scripted
```

#### 10. Run in offline mock mode

```bash
AIGB_PROVIDER=mock .venv/bin/python -m agentic_game_builder \
  --prompt "Make a traffic dodging game where the player crosses busy lanes." \
  --output-dir ./generated_games/mock-smoke
```

#### 11. Open the generated game

```bash
open generated_games/mock-smoke/index.html
```

### Windows Command Prompt

#### 1. Open the repo

```bat
cd /d C:\Users\Admin\Documents\AI-Game-builder
```

#### 2. Create the virtual environment

```bat
uv venv .venv
```

#### 3. Activate the environment

```bat
call .venv\Scripts\activate
```

#### 4. Install the project into the environment

```bat
uv pip install -e .
```

If you do not want to activate the environment, use `.venv\Scripts\python.exe` directly.

#### 5. Verify the resolved model routing

```bat
.venv\Scripts\python.exe -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

#### 6. Run interactively

```bat
.venv\Scripts\python.exe -m agentic_game_builder
```

#### 7. Run with a direct prompt

```bat
.venv\Scripts\python.exe -m agentic_game_builder ^
  --prompt "Make a cyber heist game about stealing data from a neon vault."
```

#### 8. Run with a fixed output directory

```bat
.venv\Scripts\python.exe -m agentic_game_builder ^
  --prompt "Create a jungle relic collection game." ^
  --output-dir .\generated_games\jungle-demo
```

#### 9. Run with an answers file

```bat
.venv\Scripts\python.exe -m agentic_game_builder ^
  --prompt "Make a cyber heist game about stealing data." ^
  --answers-file .\answers.json ^
  --output-dir .\generated_games\heist-scripted
```

#### 10. Run in offline mock mode

```bat
set AIGB_PROVIDER=mock
.venv\Scripts\python.exe -m agentic_game_builder ^
  --prompt "Make a traffic dodging game where the player crosses busy lanes." ^
  --output-dir .\generated_games\mock-smoke
set AIGB_PROVIDER=
```

#### 11. Open the generated game

```bat
start generated_games\mock-smoke\index.html
```

### Windows PowerShell

#### 1. Open the repo

```powershell
Set-Location "C:\Users\Admin\Documents\AI-Game-builder"
```

#### 2. Create the virtual environment

```powershell
uv venv .venv
```

#### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script in the current session, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

#### 4. Install the project into the environment

```powershell
uv pip install -e .
```

If you prefer not to activate the environment, use `.\.venv\Scripts\python.exe` directly.

#### 5. Verify the resolved model routing

```powershell
.\.venv\Scripts\python.exe -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

#### 6. Run interactively

```powershell
.\.venv\Scripts\python.exe -m agentic_game_builder
```

#### 7. Run with a direct prompt

```powershell
.\.venv\Scripts\python.exe -m agentic_game_builder `
  --prompt "Make a cyber heist game about stealing data from a neon vault."
```

#### 8. Run with a fixed output directory

```powershell
.\.venv\Scripts\python.exe -m agentic_game_builder `
  --prompt "Create a jungle relic collection game." `
  --output-dir .\generated_games\jungle-demo
```

#### 9. Run with an answers file

```powershell
.\.venv\Scripts\python.exe -m agentic_game_builder `
  --prompt "Make a cyber heist game about stealing data." `
  --answers-file .\answers.json `
  --output-dir .\generated_games\heist-scripted
```

#### 10. Run in offline mock mode

```powershell
$env:AIGB_PROVIDER = "mock"
.\.venv\Scripts\python.exe -m agentic_game_builder `
  --prompt "Make a traffic dodging game where the player crosses busy lanes." `
  --output-dir .\generated_games\mock-smoke
Remove-Item Env:\AIGB_PROVIDER
```

#### 11. Open the generated game

```powershell
Start-Process .\generated_games\mock-smoke\index.html
```

### Manual test checklist for any operating system

After a successful run:

1. open the generated output directory
2. open `index.html` in a browser
3. verify movement, win/lose conditions, score or timer behavior, and restart support
4. compare the generated game against the original prompt and clarification answers

Good manual test prompts:

- `Make a cyber heist game about stealing data from a neon vault.`
- `Make a traffic dodging game where a courier crosses busy lanes at night.`
- `Make a side-view jungle runner where an explorer jumps over traps and grabs relics.`

## Agent Architecture

### High-level flow

The agent is structured as a pipeline rather than one giant prompt:

1. The user provides a vague idea.
2. The clarification phase identifies missing implementation details.
3. The framework selector chooses `vanilla_js` or `phaser`.
4. The planning phase turns the prompt and answers into a structured game spec.
5. The generator produces `index.html`, `style.css`, and `game.js`.
6. The validator checks the generated artifacts before and after writing them.

### Multi-LLM architecture

The repo now uses role-based model routing instead of a single shared LLM path.

Current default model responsibilities:

1. Clarification and planning model:
   Groq `openai/gpt-oss-120b`
2. Code generation primary:
   OpenRouter `qwen/qwen3-coder:free`
3. Code generation fallback:
   Groq `moonshotai/kimi-k2-instruct-0905`

The design reason for this split is simple:

- clarification and planning benefit more from a stronger reasoning-oriented model
- code generation benefits from a coding-focused model
- OpenRouter free models can rate-limit, so a live fallback is needed for codegen

### Phase-by-phase architecture

#### Clarify

`agentic_game_builder/clarification.py`

Responsibilities:

- inspect the prompt
- detect missing gameplay-shaping details
- ask targeted questions about objective, perspective, controls, player role, signature mechanic, pacing, tone, and arena

Current behavior:

- try live LLM-generated clarification questions first
- filter those questions against allowed keys and prompt facts already present
- if the live response fails or is unusable, fall back to local prompt heuristics

#### Select Framework

`agentic_game_builder/framework_selector.py`

Responsibilities:

- explicitly choose between `vanilla_js` and `phaser`
- use simple prompt and answer cues such as `side-view`, `platformer`, `jump`, and physics-heavy language

This phase exists to keep the runtime decision visible and inspectable instead of burying it inside generation.

#### Plan

`agentic_game_builder/planner.py`

Responsibilities:

- combine prompt signals, clarification answers, and framework choice
- ask the design model for a structured game plan
- normalize the result into a bounded `GameSpec`
- fill gaps deterministically if the model omits fields

The planner is the bridge between vague human input and implementation-ready game structure.

The resulting spec carries:

- theme
- title
- concept summary
- objective
- perspective
- entities
- controls
- signature mechanic
- progression and tone
- win/lose conditions
- score or survival target
- runtime tuning values

#### Generate

`agentic_game_builder/generator.py`

Responsibilities:

- ask the coding model for a complete browser-game bundle
- validate the returned files immediately
- perform one repair retry if validation fails
- fall back to the built-in deterministic generator only if live generation still fails

Current live generation order:

1. OpenRouter `qwen/qwen3-coder:free`
2. Groq `moonshotai/kimi-k2-instruct-0905`
3. built-in template fallback

This is the part of the system most directly responsible for whether the output feels like the requested game or just a generic reskin.

#### Validate

`agentic_game_builder/validator.py`

Responsibilities:

- ensure required files exist
- ensure `index.html` references `style.css` and `game.js`
- ensure `game.js` contains either a vanilla loop or a Phaser bootstrap
- ensure restart support exists

Validation is intentionally lightweight. It is there to catch obvious broken bundles, not to prove gameplay quality.

### Important modules

- `agentic_game_builder/cli.py`: top-level orchestration
- `agentic_game_builder/analysis.py`: prompt heuristics and signal extraction
- `agentic_game_builder/clarification.py`: clarification question generation and fallback logic
- `agentic_game_builder/framework_selector.py`: framework routing
- `agentic_game_builder/planner.py`: structured spec building
- `agentic_game_builder/generator.py`: live codegen plus deterministic fallback
- `agentic_game_builder/llm.py`: role-based model resolution and HTTP clients
- `agentic_game_builder/output.py`: output directory and file writing
- `agentic_game_builder/validator.py`: generated artifact validation
- `tests/test_pipeline.py`: unit and end-to-end-ish pipeline coverage

## Docker Build And Run Instructions

### Shared Docker notes

- build the image from the repo root
- rebuild the image after code changes
- make sure Docker Desktop or your local Docker engine is actually running
- mount `generated_games/` into the container so outputs are preserved outside the container

### Build the Docker image on any operating system

```bash
docker build -t agentic-game-builder .
```

The command is the same on Linux, macOS, Windows Command Prompt, and Windows PowerShell. The difference comes when mounting volumes in `docker run`.

### Linux / WSL Docker commands

#### Interactive run

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --output-dir /app/generated_games/demo
```

#### Prompt-driven run

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a top-down zombie survival game." \
  --output-dir /app/generated_games/zombie-demo
```

#### Mock-mode Docker run

```bash
docker run --rm -it \
  --env AIGB_PROVIDER=mock \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a simple space survival game." \
  --output-dir /app/generated_games/mock-demo
```

#### Live Docker run using `.env`

```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make a cyber heist game about stealing data from a neon vault." \
  --output-dir /app/generated_games/live-demo
```

### macOS Docker commands

#### Interactive run

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --output-dir /app/generated_games/demo
```

#### Prompt-driven run

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a top-down zombie survival game." \
  --output-dir /app/generated_games/zombie-demo
```

#### Mock-mode Docker run

```bash
docker run --rm -it \
  --env AIGB_PROVIDER=mock \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a simple space survival game." \
  --output-dir /app/generated_games/mock-demo
```

#### Live Docker run using `.env`

```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make a cyber heist game about stealing data from a neon vault." \
  --output-dir /app/generated_games/live-demo
```

### Windows Command Prompt Docker commands

#### Interactive run

```bat
docker run --rm -it ^
  -v "%cd%\generated_games:/app/generated_games" ^
  agentic-game-builder ^
  --output-dir /app/generated_games/demo
```

#### Prompt-driven run

```bat
docker run --rm -it ^
  -v "%cd%\generated_games:/app/generated_games" ^
  agentic-game-builder ^
  --prompt "Make me a top-down zombie survival game." ^
  --output-dir /app/generated_games/zombie-demo
```

#### Mock-mode Docker run

```bat
docker run --rm -it ^
  --env AIGB_PROVIDER=mock ^
  -v "%cd%\generated_games:/app/generated_games" ^
  agentic-game-builder ^
  --prompt "Make me a simple space survival game." ^
  --output-dir /app/generated_games/mock-demo
```

#### Live Docker run using `.env`

```bat
docker run --rm -it ^
  --env-file .env ^
  -v "%cd%\generated_games:/app/generated_games" ^
  agentic-game-builder ^
  --prompt "Make a cyber heist game about stealing data from a neon vault." ^
  --output-dir /app/generated_games/live-demo
```

### Windows PowerShell Docker commands

#### Interactive run

```powershell
docker run --rm -it `
  -v "${PWD}\generated_games:/app/generated_games" `
  agentic-game-builder `
  --output-dir /app/generated_games/demo
```

#### Prompt-driven run

```powershell
docker run --rm -it `
  -v "${PWD}\generated_games:/app/generated_games" `
  agentic-game-builder `
  --prompt "Make me a top-down zombie survival game." `
  --output-dir /app/generated_games/zombie-demo
```

#### Mock-mode Docker run

```powershell
docker run --rm -it `
  --env AIGB_PROVIDER=mock `
  -v "${PWD}\generated_games:/app/generated_games" `
  agentic-game-builder `
  --prompt "Make me a simple space survival game." `
  --output-dir /app/generated_games/mock-demo
```

#### Live Docker run using `.env`

```powershell
docker run --rm -it `
  --env-file .env `
  -v "${PWD}\generated_games:/app/generated_games" `
  agentic-game-builder `
  --prompt "Make a cyber heist game about stealing data from a neon vault." `
  --output-dir /app/generated_games/live-demo
```

If Docker is unavailable in WSL, enable Docker Desktop WSL integration or run the local Python flow instead.

## Testing And Verification

### Linux / WSL

Run the full test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run a syntax check:

```bash
.venv/bin/python -m py_compile $(find agentic_game_builder tests -name '*.py')
```

Inspect the resolved live model setup:

```bash
.venv/bin/python -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

### macOS

Run the full test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run a syntax check:

```bash
.venv/bin/python -m py_compile $(find agentic_game_builder tests -name '*.py')
```

Inspect the resolved live model setup:

```bash
.venv/bin/python -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

### Windows Command Prompt

Run the full test suite:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run a syntax check:

```bat
.venv\Scripts\python.exe -m py_compile agentic_game_builder\__init__.py agentic_game_builder\__main__.py agentic_game_builder\analysis.py agentic_game_builder\clarification.py agentic_game_builder\cli.py agentic_game_builder\framework_selector.py agentic_game_builder\generator.py agentic_game_builder\llm.py agentic_game_builder\models.py agentic_game_builder\output.py agentic_game_builder\planner.py agentic_game_builder\validator.py tests\test_pipeline.py
```

Inspect the resolved live model setup:

```bat
.venv\Scripts\python.exe -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

### Windows PowerShell

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run a syntax check:

```powershell
.\.venv\Scripts\python.exe -m py_compile agentic_game_builder\__init__.py agentic_game_builder\__main__.py agentic_game_builder\analysis.py agentic_game_builder\clarification.py agentic_game_builder\cli.py agentic_game_builder\framework_selector.py agentic_game_builder\generator.py agentic_game_builder\llm.py agentic_game_builder\models.py agentic_game_builder\output.py agentic_game_builder\planner.py agentic_game_builder\validator.py tests\test_pipeline.py
```

Inspect the resolved live model setup:

```powershell
.\.venv\Scripts\python.exe -c "from agentic_game_builder.llm import resolve_role_llm_clients; clients = resolve_role_llm_clients(); print(*clients.notes, sep='\n')"
```

## Trade-offs Made

- The project is limited to small 2D browser games.
  This keeps the generation target bounded and makes the results easier to inspect, but it also means many bigger game ideas must be simplified.

- The planner still normalizes outputs into a bounded `GameSpec`.
  This reduces chaos and breakage, but it can still compress truly novel prompts into a smaller design space than a fully freeform agent would.

- Built-in deterministic fallbacks still exist.
  That helps reliability and offline testing, but if all live providers fail the final game can still fall back to a more template-like runtime.

- Validation is intentionally shallow.
  The validator catches obvious broken bundles, but it does not prove that the generated gameplay is genuinely good or faithful to the prompt.

- Generated visuals use simple shapes and CSS rather than custom assets.
  That keeps the repo self-contained and easy to run, but the visual quality ceiling is lower than an asset-backed game pipeline.

- The system optimizes for operational reliability over maximal creativity.
  This is the right trade-off for an MVP, but it means some prompts are still simplified harder than an ideal future version would allow.

## Improvements I Would Make With More Time

- Strengthen the planning schema so the design model can express richer rules, enemy behaviors, level structure, and state transitions without collapsing into a handful of runtime patterns.

- Reduce the final dependency on deterministic runtime templates by introducing smaller reusable engine primitives instead of one large fallback runtime.

- Add stronger validation for generated JavaScript.
  For example: static checks for required entities, control wiring, state transitions, and win/lose logic consistency.

- Add browser-based automated playtest checks.
  Even lightweight smoke tests in a headless browser would catch more real gameplay failures than string-based validation alone.

- Add richer repair loops for code generation.
  Right now the live codegen path gets one repair pass; a future version could support multi-step structured repair with targeted diagnostics.

- Improve observability.
  The CLI could log which model handled which phase, which fallback was used, what validation failed, and why a repair or fallback happened.

- Support more output surfaces.
  For example: exportable play reports, thumbnails, gameplay metadata, or a lightweight web UI for browsing generated games.

- Add more nuanced framework routing.
  The current framework selector is intentionally simple; a stronger planner could justify Phaser or vanilla decisions from the game plan itself.

- Use stronger paid LLMs for planning and code generation.
  The current open-source and free-model stack is good enough for an MVP, but it is still noticeably behind stronger paid models when the task is end-to-end browser-game implementation. With better commercial models, the project would likely produce more reliable game logic, fewer broken edge cases, and much higher-quality final games.
