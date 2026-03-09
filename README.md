# Agentic Game Builder MVP

`Agentic Game Builder MVP` is a CLI-first project that takes an ambiguous browser game idea, asks a few clarification questions, prints a structured implementation plan, and generates a small playable `index.html`, `style.css`, and `game.js` game bundle.

The repo intentionally keeps the workflow explicit:

1. Clarify
2. Plan
3. Generate
4. Validate

The generated games are constrained to small 2D canvas-based browser games so the output stays understandable and reliable for assignment review.

## Architecture

The implementation is split into small modules:

- `agentic_game_builder/cli.py`: CLI entrypoint and phase orchestration
- `agentic_game_builder/clarification.py`: detects missing implementation details and asks targeted questions
- `agentic_game_builder/planner.py`: converts prompt + answers into a bounded game spec
- `agentic_game_builder/generator.py`: generates `index.html`, `style.css`, and `game.js`
- `agentic_game_builder/validator.py`: validates generated content and written files
- `agentic_game_builder/output.py`: manages output directory creation and file writes
- `agentic_game_builder/llm.py`: provider-agnostic LLM layer with `mock` and `openai_compatible` modes

## LLM Strategy

The architecture is provider-agnostic. The repo now loads local LLM settings from `.env` by default and is configured for OpenRouter with `qwen/qwen3-coder:free`.

Supported modes:

- `AIGB_PROVIDER=mock`
  - offline fallback mode
  - no network or API key required
  - deterministic title/summary generation
- `AIGB_PROVIDER=openai_compatible`
  - expects an OpenAI-compatible chat completions endpoint
  - configure with:
    - `AIGB_API_KEY`
    - `AIGB_MODEL`
    - `AIGB_BASE_URL`

Example:

```bash
cp .env .env.local-backup
export AIGB_PROVIDER=openai_compatible
export AIGB_API_KEY=your_key_here
export AIGB_MODEL=qwen/qwen3-coder:free
export AIGB_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

The app auto-loads `.env` at startup. Keep `.env` out of version control.

## Local Run

No third-party Python packages are required.

Interactive run:

```bash
python3 -m agentic_game_builder
```

Prompt-driven run:

```bash
python3 -m agentic_game_builder --prompt "Make me a simple space survival game."
```

Write to a specific output directory:

```bash
python3 -m agentic_game_builder \
  --prompt "Create a jungle relic collection game." \
  --output-dir ./generated_games/jungle-demo
```

Use a JSON answers file for scripted demos:

```json
{
  "perspective": "top-down",
  "controls": "arrow keys",
  "lose_condition": "Lose if an asteroid touches the player."
}
```

```bash
python3 -m agentic_game_builder \
  --prompt "Make me a simple space survival game." \
  --answers-file ./answers.json
```

## Docker

Build the image:

```bash
docker build -t agentic-game-builder .
```

Run interactively and write output into a mounted local folder:

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --output-dir /app/generated_games/demo
```

Run with a prompt argument:

```bash
docker run --rm -it \
  -v "$(pwd)/generated_games:/app/generated_games" \
  agentic-game-builder \
  --prompt "Make me a top-down zombie survival game." \
  --output-dir /app/generated_games/zombie-demo
```

## Example Flow

Input prompt:

```text
Make me a simple space survival game.
```

Typical clarification:

- Should the game be top-down, side-view, or static-screen?
- What controls should the player use?
- What should cause the player to lose or fail?

Typical generated output:

- `index.html`
- `style.css`
- `game.js`

The result is a local canvas game with player movement, hazards, win/lose logic, and restart support.

## Validation

The validator checks:

- all required files exist
- HTML references `style.css` and `game.js`
- `game.js` includes a `requestAnimationFrame` loop
- restart capability is present

## Testing

Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

## Trade-offs

- The generator is constrained to small 2D canvas games rather than broad game genres.
- Reliability comes from a bounded game spec instead of a large freeform generation surface.
- The mock provider keeps the repo reproducible offline, but a real provider can be plugged in through the LLM abstraction.
- The output uses placeholder visuals and simple geometry instead of assets or external frameworks.

## Future Improvements

- richer game-spec normalization
- browser-based preview or playtest automation
- stronger generated JavaScript validation
- additional LLM providers
- iterative repair when generated output fails checks
