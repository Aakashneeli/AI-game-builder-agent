# Agentic Game Builder MVP Tasks

1. Set up the Python CLI project and core workflow entrypoint.
2. Define the shared game spec used between clarification, planning, generation, and validation.
3. Build the clarification phase that asks only the missing implementation-critical questions.
4. Build the planning phase that turns vague prompts into a bounded 2D canvas game spec.
5. Build the code generator that writes `index.html`, `style.css`, and `game.js`.
6. Add validation to confirm the required files and runtime references are present.
7. Add Docker support so the workflow can be reproduced in a container.
8. Write the README with architecture, usage, trade-offs, and example runs.
9. Test the full flow with a few ambiguous prompts and verify the generated game opens locally.
