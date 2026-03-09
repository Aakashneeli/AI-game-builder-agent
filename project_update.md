# Project Update

This file tracks the current state of the project, what has been implemented, what has been tested, what failed during development, and what was fixed. It should be updated after each significant feature, bug fix, or workflow change.

## Latest Update Summary

Most recent product and workflow updates:

- expanded the clarification phase beyond only missing basics so it can now ask about:
  - player identity
  - signature mechanic
  - progression style
  - visual tone
  - arena detail
- expanded the game spec so those answers survive planning and generation instead of being lost after clarification
- updated generation to use personalization fields for:
  - HUD flavor copy
  - tone-aware palette changes
  - pressure curves
  - hazard-pattern changes
  - simple ability hooks such as dash, shield, blink, magnet pull, and double jump
- updated the CLI so extra `--answers-file` keys are still passed through to planning even when the capped question list does not explicitly ask for them
- updated `README.md` and `AGENTS.md` to document the richer personalization flow

Recent behaviors reduced or replaced:

- reduced the old tendency to turn many prompts into the same reskinned runtime
- replaced the narrower “ask only the missing minimum” clarification behavior with a more expressive but still bounded personalization pass
- kept the explicit 5-phase flow:
  - clarify
  - select framework
  - plan
  - generate
  - validate

## Current Project Status

The project is currently at a working MVP stage.

Implemented:

- Python CLI agent for browser game generation
- Explicit workflow phases:
  - clarify
  - select framework
  - plan
  - generate
  - validate
- Structured game-spec planning flow
- richer clarification and personalization capture
- Browser game output generation for:
  - `index.html`
  - `style.css`
  - `game.js`
- runtime personalization hooks for pacing, tone, and simple abilities
- Output folder management
- Basic validation checks for generated files
- Docker support
- README documentation
- `AGENTS.md` setup and run guide
- `tasks.md` with a concise phase-based task list
- Git repository initialization and GitHub push

## Main Files Added

- `agentic_game_builder/cli.py`
- `agentic_game_builder/clarification.py`
- `agentic_game_builder/framework_selector.py`
- `agentic_game_builder/planner.py`
- `agentic_game_builder/generator.py`
- `agentic_game_builder/validator.py`
- `agentic_game_builder/output.py`
- `agentic_game_builder/llm.py`
- `README.md`
- `AGENTS.md`
- `tasks.md`
- `Dockerfile`
- `tests/test_pipeline.py`

## What Was Built

### 1. CLI Agent

A Python CLI entrypoint was created to run the full agent workflow from terminal input.

Supported usage:

- interactive prompt entry
- direct `--prompt`
- `--output-dir`
- `--answers-file`

### 2. Clarification Phase

A clarification manager was added to:

- inspect the user prompt
- identify missing implementation-critical details
- ask focused personalization questions when needed

The clarification flow now asks about more than just minimum viability. It can capture:

- player identity
- signature hook
- pacing / escalation style
- visual mood
- arena detail

### 3. Planning Phase

A planner was implemented to normalize vague prompts into a bounded game specification.

The spec includes:

- title
- theme
- framework
- mechanic
- player identity
- signature mechanic
- progression style
- visual tone
- arena detail
- player ability
- pressure curve
- hazard pattern
- controls
- entities
- scoring
- win condition
- lose condition
- rendering approach
- output files

### 4. Code Generation

A generator was implemented to create:

- `index.html`
- `style.css`
- `game.js`

The generated game is a small 2D HTML5 canvas game with:

- player movement
- hazards
- optional collectibles
- score or survival logic
- win/lose handling
- restart support
- personalized HUD flavor text
- tone-influenced palette changes
- prompt-driven pacing changes
- prompt-driven simple ability hooks

The generator now supports:

- vanilla JavaScript output
- Phaser output for framework-selected prompts

Older behavior replaced:

- one mostly uniform runtime template for many prompt types

### 5. Validation

Validation was added for:

- required files present
- HTML references to CSS and JS
- JS contains either a vanilla loop or a Phaser bootstrap
- restart functionality present
- output directory written correctly

### 6. Docker Support

A Dockerfile was added so the project can be built and run in a container.

### 7. Documentation

Added:

- `README.md`
- `AGENTS.md`
- `tasks.md`

These explain:

- local setup
- virtual environment usage
- `uv` usage
- running the project
- Docker usage
- testing flow

## LLM / API Configuration

The project was updated to load configuration from a local `.env` file.

Current default setup:

- provider chain:
  - Groq `openai/gpt-oss-120b`
  - Groq `qwen/qwen3-32b`
  - OpenRouter fallback

Implemented in:

- `agentic_game_builder/llm.py`

Security handling:

- `.env` is gitignored
- `.env.*` is gitignored
- `.venv/` is gitignored

## Tests Run

The following checks were run successfully during development:

### Python compile check

```bash
python3 -m py_compile $(rg --files -g '*.py')
```

### Unit tests

```bash
python3 -m unittest discover -s tests -v
```

These tests verify:

- clarification question behavior
- planner normalization
- generation of required files
- validation success for generated output

### End-to-end CLI generation test

A full CLI run was completed successfully using:

- prompt input
- clarification answers
- output directory generation

The CLI generated:

- `index.html`
- `style.css`
- `game.js`

and reported successful validation.

### Personalized mock smoke tests

Additional mock CLI runs were completed successfully for:

- a personalized cyber heist prompt with a dash ability and mysterious tone
- a side-view jungle runner prompt with a double-jump hook and playful tone

Observed results:

- clarification asked for personalization fields instead of only the old generic minimum
- the final plan preserved player identity, signature mechanic, pacing, tone, and arena detail
- generated output included different runtime config for abilities and pressure curves
- the Phaser-selected prompt still completed cleanly through the full 5-phase pipeline

### Live provider fallback test

A real CLI run was executed against the configured OpenRouter setup with:

- model: `qwen/qwen3-coder:free`
- scripted clarification answers
- output directory: `/tmp/aigb-live-run-fixed`

Observed behavior:

- OpenRouter returned `HTTP 429 Too Many Requests`
- the CLI printed a clear provider failure message
- the CLI fell back to the deterministic mock client
- the full generation pipeline still completed successfully

Generated files confirmed on disk:

- `index.html`
- `style.css`
- `game.js`

### Groq-first provider-chain validation

The live provider configuration was later changed to:

1. Groq `openai/gpt-oss-120b`
2. Groq `qwen/qwen3-32b`
3. OpenRouter fallback

Validation results:

- the provider chain resolved correctly in the runtime
- a live CLI run completed successfully using `Groq openai/gpt-oss-120b`
- the CLI now prints which live provider/model generated the plan copy
- generated files were written successfully to `/tmp/aigb-groq-chain-run-3`

### Variant runtime validation

Additional validation was performed with mock-mode generations for:

- a traffic lane-dodging prompt
- a side-view jungle runner prompt

Observed result:

- the planner selected different `play_variant` values
- the generated `game.js` files included different movement and arena modes
- the traffic prompt resolved to a lane-based dodger with cars
- the side-view prompt resolved to a ground-strip runner with jump behavior

### Framework-selection phase validation

A mock CLI run was executed with a side-view jungle runner prompt.

Observed result:

- the CLI displayed a dedicated `Select Framework` phase
- the framework selector chose `phaser`
- the plan included `framework: "phaser"`
- generation completed successfully with framework-specific output

### Documentation / operator-guide update

The repo operator documentation was expanded in `AGENTS.md` to include:

- `uv` install commands
- virtual-environment creation and activation commands
- editable install command
- direct run commands
- mock-mode run command
- direct venv-python command
- full test suite command
- single-test-module command
- syntax-check command
- provider-resolution inspection command
- Docker build and run commands
- Docker mock-mode command

## Issues Encountered During Development

### 1. JavaScript template generation bug

Issue:

- Python `string.Template` conflicted with JavaScript template-literal syntax in `game.js`

Impact:

- generation test failed

Fix:

- replaced JS template substitution with a plain marker replacement approach

Status:

- fixed

### 2. CLI answers-file failure mode

Issue:

- invalid or missing `--answers-file` path caused a raw traceback

Fix:

- added CLI error handling for file-read and JSON parsing failures

Status:

- fixed

### 3. Mixed git / push setup issues

Issue:

- project directory was not initially a git repository
- HTTPS push first failed due to missing network access in sandbox
- later HTTPS push failed due to missing GitHub credentials
- SSH push failed because SSH was not configured in the shell environment

Fix:

- initialized a git repo on `main`
- added remote
- used HTTPS with a PAT to complete the push

Status:

- fixed

### 4. WSL Python command issue on user machine

Issue:

- `python` resolved to a broken Windows `pyenv-win` shim in WSL

Fix / guidance given:

- use `python3` to create the venv
- activate `.venv`
- then use the venv’s `python`

Status:

- workaround provided

### 5. `uv` missing on user machine

Issue:

- `uv` was not installed initially

Fix / guidance given:

- either install `uv`
- or use standard `venv` temporarily

Status:

- user later ran `uv pip install -e .` successfully inside `.venv`

### 6. OpenRouter free-model rate limit crash

Issue:

- live CLI execution against OpenRouter returned `HTTP 429 Too Many Requests`
- the CLI crashed during planning with a traceback instead of recovering cleanly

Fix:

- added transient retry handling for LLM requests
- added provider error classification in the LLM layer
- added CLI fallback to the deterministic mock LLM when live plan-copy generation fails
- kept the rest of the generation pipeline running so the user still gets output

Status:

- fixed

### 7. Generic clarification wording

Issue:

- follow-up questions were structurally correct but too generic
- different prompt types still received nearly the same clarification wording

Fix:

- updated the clarification manager to build question wording from prompt context
- question prompts now reflect detected theme, mechanic, likely player entity, and likely hazards or pickups
- added regression tests to ensure space and jungle prompts generate contextualized questions

Status:

- fixed

### 8. Single-provider default LLM routing

Issue:

- the runtime defaulted to a single OpenRouter model
- the desired behavior is Groq-first with ordered provider/model fallback

Fix:

- changed the default LLM resolution to a provider chain
- added Groq primary and secondary model support
- kept OpenRouter as the next live fallback
- preserved the deterministic mock fallback after all live providers fail
- added regression coverage for multi-provider fallback sequencing

Status:

- fixed

### 9. Same runtime template for most prompts

Issue:

- many different prompts still produced nearly the same game loop and entity behavior
- the planner changed labels, but the generated runtime still behaved like one template

Fix:

- extended the game spec with explicit gameplay-variant fields
- added variant selection in the planner
- updated the generator to emit materially different runtime behavior for:
  - arena survival
  - collector rush
  - collector escape / chase escape
  - lane dodger
  - side runner
- added regression tests to confirm different prompts map to different variants

Status:

- fixed

### 10. Non-interactive clarification EOF failure

Issue:

- scripted CLI runs with an incomplete `--answers-file` crashed with `EOFError`

Fix:

- added a clear CLI error message when a required clarification answer is missing in non-interactive execution

Status:

- fixed

### 11. Framework choice was implicit instead of a phase

Issue:

- the project hardcoded framework behavior inside planning and generation
- the CLI did not expose framework choice as a distinct agent step

Fix:

- added a dedicated framework selector module
- added a visible `Select Framework` phase in the CLI
- threaded the framework decision into the plan and code generation
- added Phaser generation support for framework-selected prompts

Status:

- fixed

### 12. Missing operator commands in AGENTS.md

Issue:

- `AGENTS.md` did not contain enough execution detail for setup, testing, verification, and troubleshooting

Fix:

- added explicit shell commands for environment setup, dependency installation, activation, running, testing, syntax checks, provider inspection, and Docker usage
- added niche operator notes for WSL `python` issues, mock-mode testing, incomplete answers files, and Phaser CDN behavior

Status:

- fixed

### 13. Repetitive prompt-to-runtime collapse

Issue:

- too many different prompts still felt like the same game with renamed labels
- clarification captured too little information to personalize the result

Fix:

- expanded clarification with prompt-aware personalization questions
- expanded the shared game spec to preserve those answers
- added runtime modifiers for ability hooks, pressure curves, hazard patterns, HUD flavor text, and tone-aware palette changes

Status:

- fixed

### 14. Extra answers-file fields were ignored

Issue:

- values present in `--answers-file` were ignored unless that exact question appeared in the capped clarification list
- this blocked scripted personalized runs from fully shaping the plan

Fix:

- changed the CLI to seed planning answers from the entire answers file first
- interactive clarification still overrides or fills missing values, but unprompted answers-file keys now survive into planning

Status:

- fixed

## Git / Repo Status

The project was pushed to:

- `https://github.com/Aakashneeli/AI-game-builder-agent.git`

Branch:

- `main`

Initial pushed commit:

- `82c57e2` `Initial project setup`

## Important Notes

- The repo currently uses a local `.env` file for model configuration.
- Sensitive values must never be committed.
- A GitHub PAT was used during one push flow in chat context; that token should be revoked and replaced if it is still active.

## Next Update Policy

This file should be updated whenever any of the following happens:

- a new feature is added
- a bug is fixed
- a test is added or changed
- Docker behavior changes
- setup instructions change
- model/provider configuration changes
- deployment or git workflow changes

## Current Open Items

- confirm real end-to-end generation against the live OpenRouter model in the user environment when the free model is not rate-limited
- test Docker build and run on the user machine
  - Docker was not available in the current WSL environment used for validation
- continue feature work based on next requirements
