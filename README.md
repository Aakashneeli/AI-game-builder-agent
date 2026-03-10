# Agentic Game Builder MVP

`Agentic Game Builder MVP` is a CLI-first project that takes an ambiguous browser game idea, asks targeted clarification questions, prints a structured implementation plan, and generates a small playable `index.html`, `style.css`, and `game.js` game bundle.

The repo intentionally keeps the workflow explicit:

1. Clarify
2. Select Framework
3. Plan
4. Generate
5. Validate

The generated games are constrained to small 2D browser games so the output stays understandable and reliable for assignment review, but the clarification and planning flow now tries to preserve more of the original prompt's personality.

## Architecture

The implementation is split into small modules:

- `agentic_game_builder/cli.py`: CLI entrypoint and phase orchestration
- `agentic_game_builder/clarification.py`: detects missing implementation details and asks targeted questions about role, signature hook, pacing, tone, and arena details
  - when a live LLM client is available, it can propose structured clarification questions first
  - if that fails or returns unusable data, the repo falls back to local prompt heuristics
- `agentic_game_builder/framework_selector.py`: explicitly chooses between vanilla JS and Phaser as an agent phase
- `agentic_game_builder/planner.py`: uses a design-model planning pass first, then normalizes the result into a bounded game spec with deterministic fallbacks
- `agentic_game_builder/generator.py`: asks a coding model for a full `index.html`, `style.css`, and `game.js` bundle first, then falls back to the built-in generator if live code generation fails validation
- `agentic_game_builder/validator.py`: validates generated content and written files
- `agentic_game_builder/output.py`: manages output directory creation and file writes
- `agentic_game_builder/llm.py`: role-based LLM resolution for design vs code generation, plus mock and OpenAI-compatible adapters

## LLM Strategy

The default runtime is now role-based rather than one shared provider chain.

Default roles:

1. Clarification and planning: Groq `openai/gpt-oss-120b`
2. Code generation and repair: OpenRouter `qwen/qwen3-coder:free`

This split keeps prompt analysis and design work on the stronger reasoning model, while the coding model focuses on generating the actual browser-game bundle.

If either live role fails hard enough, the CLI still falls back to deterministic local behavior so offline tests remain reproducible:

- clarification falls back to local heuristics
- planning falls back to deterministic mock copy plus deterministic normalization
- code generation falls back to the built-in template runtime

The live flow now looks like this:

- Groq GPT-OSS asks prompt-specific clarification questions
- Groq GPT-OSS produces a structured game plan
- OpenRouter Qwen3-Coder generates the final browser game bundle
- generated bundles are validated and get one repair retry if they miss required runtime hooks
- only after that does the repo fall back to the built-in deterministic generator

Supported modes:

- `AIGB_PROVIDER=mock`
  - offline fallback mode
  - no network or API key required
  - deterministic planning copy and built-in template generation
- live role-based mode
  - clarification/planning use `AIGB_GROQ_*`
  - code generation uses `AIGB_OPENROUTER_*`
  - optional overrides exist via `AIGB_DESIGN_*` and `AIGB_CODEGEN_*`

Example:

```bash
export AIGB_GROQ_API_KEY=your_groq_key_here
export AIGB_GROQ_PRIMARY_MODEL=openai/gpt-oss-120b
export AIGB_GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
export AIGB_OPENROUTER_API_KEY=your_openrouter_key_here
export AIGB_OPENROUTER_MODEL=qwen/qwen3-coder:free
export AIGB_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
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

## Personalization

The clarification step is no longer limited to only theme, controls, and lose condition. For prompts that need more shape, the CLI can now ask about:

- who or what the player controls
- the main playable verb
- the game's signature twist or ability
- how challenge should ramp up
- the tone or mood
- the specific arena or location

Those answers now flow into the plan and runtime. They affect things like:

- player identity and HUD copy
- arena description and visual tone
- ability hooks such as dash, shield, blink, magnet pull, or double jump
- pressure curves such as steady pacing, ramps, waves, or finale spikes
- hazard patterns that feel less like one shared template

## Example Flow

Input prompt:

```text
Make a cyber heist game about stealing data.
```

Typical clarification:

- What should the player mainly do moment to moment?
- Who or what should the player control?
- What single twist should make this version feel like yours?
- How should the challenge build over time?
- What mood should the game lean into?

Typical generated output:

- `index.html`
- `style.css`
- `game.js`

The result is a local browser game with player movement, hazards, win/lose logic, restart support, and more prompt-specific flavor in the generated rules, pacing, HUD copy, and mechanics. The framework decision is made as part of the agent workflow.

## Validation

The validator checks:

- all required files exist
- HTML references `style.css` and `game.js`
- `game.js` includes either a vanilla render loop or a Phaser bootstrap
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
- The output uses placeholder visuals and simple geometry instead of custom assets.

## Future Improvements

- richer game-spec normalization
- browser-based preview or playtest automation
- stronger generated JavaScript validation
- additional LLM providers
- iterative repair when generated output fails checks
