# Product Requirements Document (PRD)

## Product Name
Agentic Game-Builder AI (MVP)

## Version
MVP / v0.1

## Document Purpose
This PRD defines the minimum viable product for an agentic AI system that accepts an ambiguous natural-language game idea, clarifies requirements, plans the implementation, and generates a small playable HTML/CSS/JavaScript game that runs locally in a browser. The system must also be packaged in Docker and include clear documentation.

---

## 1. Product Summary
The product is a developer-facing AI agent that turns a rough game idea into a runnable browser game. The agent must not behave like a one-shot code generator. Instead, it must demonstrate a reliable multi-phase workflow:

1. Clarify the game request with targeted follow-up questions.
2. Produce a structured internal implementation plan.
3. Generate runnable files: `index.html`, `style.css`, and `game.js`.
4. Package the workflow so it can be run inside Docker.

The MVP is designed specifically to satisfy the assignment requirements with the simplest architecture that still clearly demonstrates agent behavior, control flow, and engineering discipline.

---

## 2. Problem Statement
Most code-generation demos jump directly from prompt to output. This assignment instead requires an agentic system that can manage ambiguity, gather missing requirements, make implementation decisions, and generate a working result in a controlled manner.

The core problem this product solves is:

**How can we build a lightweight but reliable agent that transforms a vague game concept into a playable browser game through explicit clarification, planning, and execution phases?**

---

## 3. Goal
Build a working MVP of an agentic game-generation system that:

- accepts a vague game idea,
- asks only the necessary follow-up questions,
- creates a structured plan,
- generates a simple playable game,
- produces local runnable output,
- and can be executed from Docker.

---

## 4. Non-Goals
To keep the project at MVP stage, the following are explicitly out of scope:

- advanced graphics pipelines,
- multiplayer support,
- asset generation pipelines,
- audio synthesis,
- persistent save systems,
- mobile optimization,
- live game preview during generation,
- multiple framework backends in the first version,
- autonomous bug-fixing loops beyond basic validation,
- production-grade hosting or cloud deployment.

The purpose is not to build a full commercial game engine, but a compact, clear proof of agentic design.

---

## 5. Target User
### Primary User
A reviewer, instructor, or developer who wants to run the agent locally and verify that it can generate a browser game from an ambiguous prompt.

### User Characteristics
- Comfortable running terminal commands
- Wants reproducible output
- Evaluates system structure, not only generated code
- Expects Docker support and documentation

---

## 6. User Journey
### Input
The user provides a vague idea such as:

> “Make me a simple space survival game.”

### Agent Flow
1. The agent analyzes the request for ambiguity.
2. The agent asks a small set of focused clarification questions.
3. The user answers those questions.
4. The agent generates a structured game plan.
5. The agent chooses implementation details.
6. The agent writes `index.html`, `style.css`, and `game.js`.
7. The output is saved to a local folder.
8. The user opens `index.html` in a browser and plays the game.

---

## 7. MVP Scope
### In Scope
The MVP must support:

- a single game generation flow per run,
- text-based natural-language input,
- clarification phase before coding,
- structured planning output,
- generation of exactly these core files:
  - `index.html`
  - `style.css`
  - `game.js`
- browser-playable local output,
- Dockerized execution,
- README with architecture and run instructions.

### Constraints for MVP
- Generate **small 2D games only**.
- Use **vanilla JavaScript by default** for simplicity and portability.
- Support only a limited set of mechanics that are easy to generate reliably, such as:
  - player movement,
  - enemy avoidance or collection,
  - score tracking,
  - win/lose conditions,
  - restart flow.
- Use placeholder visuals only (HTML/CSS/canvas shapes).
- Ask a maximum of a few relevant follow-up questions before proceeding.

---

## 8. Product Principles
The MVP should follow these principles:

### 1. Reliability over complexity
Prefer a smaller set of supported game patterns that generate consistently.

### 2. Explicit agent workflow
The system should visibly separate clarification, planning, and execution.

### 3. Minimal but playable output
The generated game does not need polish, but it must run and be understandable.

### 4. Low operational friction
A reviewer should be able to build and run it with straightforward Docker commands.

### 5. No manual intervention in generated files
The game output should come entirely from the agent workflow.

---

## 9. Functional Requirements

### FR1. Accept natural-language game idea
The system shall accept a user-provided game prompt as input.

### FR2. Detect ambiguity
The system shall identify missing requirements that block implementation, such as:
- goal of the game,
- player controls,
- win/lose conditions,
- preferred theme,
- complexity level.

### FR3. Ask clarifying questions
The system shall ask focused follow-up questions before code generation.

#### Clarification requirements
- Questions must be relevant.
- Questions must be limited in number.
- Questions should stop once enough information exists to generate a basic game.

### FR4. Produce a structured plan
The system shall generate a machine-readable or clearly structured implementation plan before coding.

The plan should include:
- game concept summary,
- chosen framework,
- controls,
- game loop,
- entities,
- scoring,
- win/lose conditions,
- file structure,
- technical approach.

### FR5. Choose implementation stack
The system shall choose between Phaser or vanilla JS.

#### MVP decision
For the MVP, the system should default to **vanilla JS + HTML5 Canvas** unless a strong reason exists otherwise.

### FR6. Generate runnable files
The system shall generate:
- `index.html`
- `style.css`
- `game.js`

### FR7. Ensure local playability
The generated game shall run locally in a browser without requiring external backend services.

### FR8. Save output to local directory
The system shall write the generated files into a target output folder.

### FR9. Provide Docker support
The system shall be runnable inside a Docker container.

### FR10. Provide README
The project shall include a `README.md` describing:
- how to run the agent,
- agent architecture,
- trade-offs,
- possible future improvements,
- Docker build instructions,
- Docker run instructions.

---

## 10. Non-Functional Requirements

### NFR1. Understandability
The architecture and generated artifacts should be easy for a reviewer to inspect.

### NFR2. Deterministic workflow shape
Even if generation is not fully deterministic, the control flow should always follow:
**clarify → plan → generate**.

### NFR3. Fast local execution
The MVP should complete a single generation run quickly under normal local conditions.

### NFR4. Minimal dependencies
The implementation should use as few moving pieces as possible.

### NFR5. Reproducibility
A reviewer should be able to run the same Docker commands and obtain the full workflow.

---

## 11. Recommended MVP Product Design

### 11.1 Interface
A simple CLI interface is sufficient for the MVP.

Example flow:

1. User runs the agent command.
2. User enters the initial game prompt.
3. Agent asks follow-up questions in the terminal.
4. Agent prints the plan.
5. Agent generates files in an output folder.

### 11.2 Suggested Internal Modules
To make the system clearly agentic, structure it into modules such as:

- **Input Handler**
  - collects initial prompt and answers
- **Clarification Manager**
  - determines what is missing
  - asks follow-up questions
- **Planner**
  - creates structured game spec
- **Framework Selector**
  - picks vanilla JS for MVP
- **Code Generator**
  - writes HTML/CSS/JS files
- **Validator**
  - performs basic checks such as file existence and required symbols
- **Output Manager**
  - saves files to disk

This modular breakdown helps demonstrate engineering structure even in a small project.

---

## 12. MVP Technical Direction

### Chosen Implementation Strategy
For the MVP, the recommended path is:

- **Interface:** CLI
- **Game runtime:** HTML + CSS + vanilla JavaScript
- **Rendering:** HTML5 Canvas
- **Agent orchestration:** one controller script
- **LLM usage:** one or more calls for clarification, planning, and generation
- **Packaging:** Docker

### Why vanilla JS over Phaser for MVP
Vanilla JS is the better MVP choice because:
- fewer dependencies,
- easier offline/local execution,
- simpler generated output,
- easier Docker packaging,
- easier for reviewers to inspect.

Phaser could be a future enhancement if broader gameplay patterns are needed.

---

## 13. Supported Game Pattern for MVP
To reduce failure risk, the MVP should support a constrained family of games.

### Recommended supported patterns
- dodge-survival game,
- collect-items game,
- avoid-enemies game,
- top-down movement game,
- score-based arcade mini-game.

### Example outputs
- “Collect stars while avoiding enemies.”
- “Survive for 30 seconds in a zombie room.”
- “Move a spaceship and dodge asteroids.”

The system may reinterpret more complex prompts into a simplified playable version.

---

## 14. Clarification Strategy
The clarification phase should be intentionally narrow.

### Questions the agent may ask
The agent should try to resolve only implementation-critical ambiguities such as:
- What is the main objective?
- What controls should the player use?
- What causes the player to win or lose?
- Should the game be top-down, side-view, or static-screen?
- Should the game focus on collecting, dodging, or survival?

### Stopping rule
The agent should stop asking questions once it has enough information to define:
- player action,
- goal,
- failure condition,
- core loop,
- theme.

### MVP guardrail
Limit follow-up questions to around 3–5 unless the input is extremely vague.

---

## 15. Planning Output Requirements
The plan should be explicit and structured so the reviewer can see the reasoning path.

### Minimum plan contents
- Game title or concept
- Theme
- Core mechanic
- Controls
- Player entity
- Obstacles/enemies/items
- Scoring model
- Win condition
- Lose condition
- Rendering approach
- File structure
- Notes for code generation

A JSON-like structure or clearly labeled text is acceptable.

---

## 16. Execution Requirements
After planning, the agent must generate all code artifacts.

### Required files
#### `index.html`
Should:
- load the canvas/game container,
- reference `style.css`,
- reference `game.js`.

#### `style.css`
Should:
- provide minimal layout and styling,
- center the game or make it readable,
- style score/game-over text if needed.

#### `game.js`
Should implement:
- canvas setup,
- input handling,
- update loop,
- render loop,
- collision detection where needed,
- score/win/lose logic,
- restart capability.

---

## 17. Validation Requirements
The MVP should include lightweight validation after generation.

### Minimum validation checks
- all required files exist,
- HTML references CSS and JS correctly,
- JavaScript defines a runnable game loop,
- output folder is created successfully.

Optional lightweight checks:
- basic lint or syntax validation,
- template consistency checks,
- required sections present in generated files.

---

## 18. Docker Requirements
The solution must be Dockerized.

### Docker goals
- allow reviewers to build the image,
- run the agent inside a container,
- generate files into a mounted output directory.

### Expected Docker behavior
A reviewer should be able to:
1. build the image,
2. run the container,
3. pass input or use interactive mode,
4. retrieve generated game files.

### MVP packaging preference
Use a simple base image and minimal setup.

---

## 19. README Requirements
The `README.md` must include:

### 1. Project overview
What the agent does and what problem it solves.

### 2. Architecture
Explain the major modules and their responsibilities.

### 3. Run instructions
How to run locally and/or through Docker.

### 4. Docker instructions
How to build and run the image.

### 5. Example usage
Show sample input and expected outputs.

### 6. Trade-offs
Explain where the system was simplified for MVP.

### 7. Future improvements
Explain what would be improved with more time.

---

## 20. Success Metrics
The MVP is successful if:

1. The agent asks follow-up questions before coding.
2. The number of follow-up questions is reasonable.
3. The agent produces a visible structured plan.
4. The generated files run locally in a browser.
5. The repository includes Docker support.
6. The README is clear enough for a reviewer to reproduce the workflow.

---

## 21. Acceptance Criteria
The product will be considered complete for MVP if all of the following are true:

- A user can provide an ambiguous game prompt.
- The system asks clarification questions before generation.
- The system stops clarification once sufficient information is collected.
- The system outputs a structured plan.
- The system generates `index.html`, `style.css`, and `game.js`.
- The generated game is playable locally.
- The repository includes a working Dockerfile.
- The README includes build and run instructions.
- The generation process is automated and does not require manual code editing.

---

## 22. Risks and Trade-Offs

### Risk 1. Overly broad prompts
A vague or highly ambitious prompt may produce an unmanageable game design.

**MVP response:** constrain the output to a simple 2D mini-game.

### Risk 2. Too many clarification questions
If the agent asks too much, it feels inefficient.

**MVP response:** cap the clarification phase to essential questions only.

### Risk 3. Broken generated JavaScript
Generated code may fail if the scope is too open.

**MVP response:** restrict supported mechanics and use a predictable canvas structure.

### Risk 4. Docker complexity
Too many dependencies may make the project hard to run.

**MVP response:** keep orchestration simple and dependency count low.

### Risk 5. Reviewer confusion about “agentic” behavior
If the system appears as a simple prompt-to-code script, it may not satisfy the spirit of the assignment.

**MVP response:** make phase boundaries explicit in code, logs, and documentation.

---

## 23. Trade-Off Decisions for MVP

### Decision 1: CLI instead of web app
Chosen because it is faster to implement and easier to demo.

### Decision 2: Vanilla JS instead of Phaser
Chosen because it reduces dependency and generation complexity.

### Decision 3: Limited game patterns
Chosen to improve reliability and playability.

### Decision 4: Placeholder visuals only
Chosen to avoid asset pipeline complexity.

### Decision 5: Single-run generation flow
Chosen to keep control flow simple and explainable.

---

## 24. Future Improvements
With more time, future versions could include:

- support for Phaser as a second backend,
- richer game genres,
- automatic playtesting or browser validation,
- iterative self-repair when generated code fails,
- asset generation support,
- game design memory across runs,
- web UI for prompt and preview,
- stronger evaluation of requirement completeness,
- structured JSON game spec export.

---

## 25. Recommended Build Strategy
To keep the project achievable, the implementation should be broken into four practical layers:

### Layer 1: Orchestrator
Controls the overall flow.

### Layer 2: Clarification + Planning
Uses the LLM to gather enough information and create a spec.

### Layer 3: Code Generation
Transforms the spec into HTML/CSS/JS files.

### Layer 4: Packaging + Docs
Adds Docker, README, and sample usage.

This is enough to satisfy the assignment without overengineering.

---

## 26. Final MVP Definition
The MVP is **not** a fully autonomous game studio. It is a compact, Dockerized, CLI-based agent that reliably demonstrates:

- requirement clarification,
- structured planning,
- automated code generation,
- and local browser-playable output.

That is the correct level of ambition for this assignment.

---

## 27. Suggested One-Line Product Definition
**An MVP agentic AI that turns a vague game idea into a simple playable browser game by explicitly clarifying requirements, planning the implementation, and generating runnable HTML/CSS/JavaScript files inside a Dockerized workflow.**

