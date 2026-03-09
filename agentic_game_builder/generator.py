from __future__ import annotations

import json
from string import Template
from typing import Any

from .models import GameSpec


HTML_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="app-shell">
    <section class="panel">
      <p class="eyebrow">Agentic Game Builder MVP</p>
      <h1>${title}</h1>
      <p id="gameSummary">${summary}</p>
      <div class="hud">
        <p id="instructionLine">${instruction_text}</p>
        <p id="scoreLine">Score: 0</p>
        <p id="statusLine">${objective}</p>
      </div>
      <div class="actions">
        <button id="restartButton" type="button">Restart</button>
        <span class="hint">Press R to restart at any time.</span>
      </div>
    </section>
    <canvas id="gameCanvas" width="${width}" height="${height}" aria-label="Generated game canvas"></canvas>
  </main>
  <script src="game.js"></script>
</body>
</html>
"""
)


CSS_TEMPLATE = Template(
    """:root {
  --page-bg: ${page_bg};
  --panel-bg: ${panel_bg};
  --panel-border: ${panel_border};
  --text-main: ${text_main};
  --text-muted: ${text_muted};
  --accent: ${accent};
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  color: var(--text-main);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 32%),
    linear-gradient(180deg, ${page_bg}, #05070f 72%);
}

.app-shell {
  width: min(1120px, 100%);
  display: grid;
  gap: 20px;
  align-items: start;
}

@media (min-width: 900px) {
  .app-shell {
    grid-template-columns: 320px minmax(0, 1fr);
  }
}

.panel {
  padding: 20px;
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  background: var(--panel-bg);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
}

.eyebrow {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--accent);
  font-size: 0.74rem;
}

h1 {
  margin: 0 0 12px;
  font-size: clamp(1.8rem, 3vw, 2.4rem);
}

.hud p,
#gameSummary,
.hint {
  margin: 0 0 12px;
}

.hud {
  display: grid;
  gap: 8px;
  margin: 18px 0;
  color: var(--text-muted);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

button {
  border: 0;
  border-radius: 999px;
  padding: 12px 18px;
  cursor: pointer;
  background: var(--accent);
  color: #06111c;
  font-weight: 700;
}

canvas {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: #02050b;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
}
"""
)


JS_TEMPLATE = """const config = __CONFIG_JSON__;

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreLine = document.getElementById("scoreLine");
const statusLine = document.getElementById("statusLine");
const instructionLine = document.getElementById("instructionLine");
const restartButton = document.getElementById("restartButton");

const state = {
  screen: "running",
  score: 0,
  elapsed: 0,
  lastFrame: 0,
  keys: new Set(),
  mouse: { x: config.width / 2, y: config.height / 2, active: false },
  player: null,
  hazards: [],
  collectibles: [],
  endMessage: "",
};

function randomRange(min, max) {
  return Math.random() * (max - min) + min;
}

function makePlayer() {
  return {
    x: config.width / 2,
    y: config.height / 2,
    radius: 16,
    speed: config.playerSpeed,
    color: config.palette.player,
  };
}

function makeHazard() {
  const speedMultiplier = 0.8 + Math.random() * 0.7;
  return {
    x: randomRange(40, config.width - 40),
    y: randomRange(40, config.height - 40),
    radius: 16,
    vx: randomRange(-140, 140) * speedMultiplier,
    vy: randomRange(-140, 140) * speedMultiplier,
    color: config.palette.hazard,
  };
}

function makeCollectible() {
  return {
    x: randomRange(40, config.width - 40),
    y: randomRange(40, config.height - 40),
    radius: 10,
    color: config.palette.collectible,
  };
}

function spawnEntities() {
  state.hazards = Array.from({ length: config.hazardCount }, () => makeHazard());
  state.collectibles = Array.from({ length: config.collectibleCount }, () => makeCollectible());
}

function resetGame() {
  state.screen = "running";
  state.score = 0;
  state.elapsed = 0;
  state.lastFrame = 0;
  state.endMessage = "";
  state.player = makePlayer();
  spawnEntities();
  render();
}

function clampPlayer() {
  state.player.x = Math.min(config.width - state.player.radius, Math.max(state.player.radius, state.player.x));
  state.player.y = Math.min(config.height - state.player.radius, Math.max(state.player.radius, state.player.y));
}

function updatePlayer(dt) {
  if (config.controlMode === "mouse" && state.mouse.active) {
    const dx = state.mouse.x - state.player.x;
    const dy = state.mouse.y - state.player.y;
    const length = Math.hypot(dx, dy);
    if (length > 1) {
      const step = Math.min(length, state.player.speed * dt);
      state.player.x += (dx / length) * step;
      state.player.y += (dy / length) * step;
    }
    clampPlayer();
    return;
  }

  let dx = 0;
  let dy = 0;

  if (config.controls.left.some((key) => state.keys.has(key))) {
    dx -= 1;
  }
  if (config.controls.right.some((key) => state.keys.has(key))) {
    dx += 1;
  }
  if (config.controls.up.some((key) => state.keys.has(key))) {
    dy -= 1;
  }
  if (config.controls.down.some((key) => state.keys.has(key))) {
    dy += 1;
  }

  const length = Math.hypot(dx, dy) || 1;
  state.player.x += (dx / length) * state.player.speed * dt;
  state.player.y += (dy / length) * state.player.speed * dt;
  clampPlayer();
}

function updateHazards(dt) {
  for (const hazard of state.hazards) {
    hazard.x += hazard.vx * dt;
    hazard.y += hazard.vy * dt;

    if (hazard.x < hazard.radius || hazard.x > config.width - hazard.radius) {
      hazard.vx *= -1;
      hazard.x = Math.min(config.width - hazard.radius, Math.max(hazard.radius, hazard.x));
    }

    if (hazard.y < hazard.radius || hazard.y > config.height - hazard.radius) {
      hazard.vy *= -1;
      hazard.y = Math.min(config.height - hazard.radius, Math.max(hazard.radius, hazard.y));
    }
  }
}

function circlesOverlap(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y) <= a.radius + b.radius;
}

function endGame(screen, message) {
  state.screen = screen;
  state.endMessage = message;
}

function handleHazardCollisions() {
  if (state.hazards.some((hazard) => circlesOverlap(state.player, hazard))) {
    endGame("lose", config.loseCondition);
  }
}

function handleCollectibleCollisions() {
  state.collectibles = state.collectibles.map((collectible) => {
    if (!circlesOverlap(state.player, collectible)) {
      return collectible;
    }
    state.score += config.scorePerCollectible;
    return makeCollectible();
  });
}

function checkWinCondition() {
  if (config.scoreTarget !== null && state.score >= config.scoreTarget) {
    endGame("win", config.winCondition);
    return;
  }

  if (config.survivalSeconds !== null && state.elapsed >= config.survivalSeconds) {
    endGame("win", config.winCondition);
  }
}

function update(dt) {
  if (state.screen !== "running") {
    return;
  }

  state.elapsed += dt;
  updatePlayer(dt);
  updateHazards(dt);
  handleHazardCollisions();

  if (state.screen !== "running") {
    return;
  }

  if (config.collectibleCount > 0) {
    handleCollectibleCollisions();
  }

  checkWinCondition();
}

function drawArena() {
  const gradient = ctx.createLinearGradient(0, 0, config.width, config.height);
  gradient.addColorStop(0, config.palette.backgroundStart);
  gradient.addColorStop(1, config.palette.backgroundEnd);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, config.width, config.height);

  ctx.strokeStyle = config.palette.grid;
  ctx.lineWidth = 1;
  for (let x = 0; x <= config.width; x += 80) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, config.height);
    ctx.stroke();
  }
  for (let y = 0; y <= config.height; y += 80) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(config.width, y);
    ctx.stroke();
  }
}

function drawCircle(entity) {
  ctx.beginPath();
  ctx.arc(entity.x, entity.y, entity.radius, 0, Math.PI * 2);
  ctx.fillStyle = entity.color;
  ctx.fill();
}

function drawOverlay() {
  if (state.screen === "running") {
    return;
  }

  ctx.fillStyle = "rgba(3, 9, 18, 0.72)";
  ctx.fillRect(0, 0, config.width, config.height);
  ctx.fillStyle = "#f8fafc";
  ctx.textAlign = "center";
  ctx.font = "bold 42px Trebuchet MS";
  ctx.fillText(state.screen === "win" ? "You Win" : "Game Over", config.width / 2, config.height / 2 - 18);
  ctx.font = "20px Trebuchet MS";
  ctx.fillText(state.endMessage, config.width / 2, config.height / 2 + 18);
  ctx.fillText("Press R or the Restart button to play again.", config.width / 2, config.height / 2 + 54);
}

function renderHud() {
  scoreLine.textContent = config.scoreTarget !== null
    ? `Score: ${state.score} / ${config.scoreTarget}`
    : `Time: ${state.elapsed.toFixed(1)} / ${config.survivalSeconds ?? "--"} sec`;

  if (config.scoreTarget !== null && config.survivalSeconds !== null) {
    scoreLine.textContent += ` | Time: ${state.elapsed.toFixed(1)} sec`;
  }

  const baseStatus = state.screen === "running" ? config.objective : state.endMessage;
  statusLine.textContent = baseStatus;
  instructionLine.textContent = config.instructionText;
}

function renderLegend() {
  ctx.textAlign = "left";
  ctx.font = "16px Trebuchet MS";
  ctx.fillStyle = "#dbeafe";
  ctx.fillText(`Player: ${config.playerEntity}`, 18, 28);
  ctx.fillText(`Hazards: ${config.hazardEntity}`, 18, 50);
  if (config.collectibleEntity) {
    ctx.fillText(`Collectibles: ${config.collectibleEntity}`, 18, 72);
  }
}

function render() {
  drawArena();
  renderLegend();
  for (const collectible of state.collectibles) {
    drawCircle(collectible);
  }
  for (const hazard of state.hazards) {
    drawCircle(hazard);
  }
  drawCircle(state.player);
  drawOverlay();
  renderHud();
}

function frame(timestamp) {
  if (!state.lastFrame) {
    state.lastFrame = timestamp;
  }
  const dt = Math.min(0.033, (timestamp - state.lastFrame) / 1000);
  state.lastFrame = timestamp;
  update(dt);
  render();
  window.requestAnimationFrame(frame);
}

window.addEventListener("keydown", (event) => {
  state.keys.add(event.key);
  if (event.key.toLowerCase() === "r") {
    resetGame();
  }
});

window.addEventListener("keyup", (event) => {
  state.keys.delete(event.key);
});

canvas.addEventListener("mousemove", (event) => {
  const rect = canvas.getBoundingClientRect();
  state.mouse.x = ((event.clientX - rect.left) / rect.width) * config.width;
  state.mouse.y = ((event.clientY - rect.top) / rect.height) * config.height;
  state.mouse.active = true;
});

canvas.addEventListener("mouseleave", () => {
  state.mouse.active = false;
});

restartButton.addEventListener("click", resetGame);

resetGame();
window.requestAnimationFrame(frame);
"""


class CodeGenerator:
    def generate(self, spec: GameSpec) -> dict[str, str]:
        config = self._build_js_config(spec)
        instruction_text = self._build_instruction_text(spec)
        html = HTML_TEMPLATE.substitute(
            title=spec.title,
            summary=spec.concept_summary,
            instruction_text=instruction_text,
            objective=spec.objective,
            width=str(spec.arena_width),
            height=str(spec.arena_height),
        )
        css = CSS_TEMPLATE.substitute(**self._palette(spec)["css"])
        js = JS_TEMPLATE.replace("__CONFIG_JSON__", json.dumps(config, indent=2))
        return {
            "index.html": html,
            "style.css": css,
            "game.js": js,
        }

    def _build_js_config(self, spec: GameSpec) -> dict[str, Any]:
        palette = self._palette(spec)["js"]
        control_mode = self._control_mode(spec)
        return {
            "title": spec.title,
            "width": spec.arena_width,
            "height": spec.arena_height,
            "objective": spec.objective,
            "instructionText": self._build_instruction_text(spec),
            "controlMode": control_mode,
            "controls": self._resolve_controls(spec.controls),
            "playerEntity": spec.player_entity,
            "hazardEntity": spec.hazard_entity,
            "collectibleEntity": spec.collectible_entity,
            "hazardCount": spec.hazard_count,
            "collectibleCount": spec.collectible_count,
            "playerSpeed": spec.player_speed,
            "scoreTarget": spec.score_target,
            "survivalSeconds": spec.survival_seconds,
            "scorePerCollectible": spec.score_per_collectible,
            "winCondition": spec.win_condition,
            "loseCondition": spec.lose_condition,
            "palette": palette,
        }

    def _build_instruction_text(self, spec: GameSpec) -> str:
        if self._control_mode(spec) == "mouse":
            return "Move the mouse inside the arena to steer the player."
        return (
            "Move with "
            f"{spec.controls['up']} / {spec.controls['left']} / {spec.controls['down']} / {spec.controls['right']}."
        )

    def _control_mode(self, spec: GameSpec) -> str:
        if any("mouse" in value.lower() for value in spec.controls.values()):
            return "mouse"
        return "keyboard"

    def _resolve_controls(self, controls: dict[str, str]) -> dict[str, list[str]]:
        resolved: dict[str, list[str]] = {}
        for direction, value in controls.items():
            lower_value = value.lower()
            keys: list[str] = []
            if "arrowup" in lower_value:
                keys.append("ArrowUp")
            if "arrowdown" in lower_value:
                keys.append("ArrowDown")
            if "arrowleft" in lower_value:
                keys.append("ArrowLeft")
            if "arrowright" in lower_value:
                keys.append("ArrowRight")
            for key in ("w", "a", "s", "d"):
                if key in lower_value:
                    keys.extend([key, key.upper()])
            if not keys:
                keys = [value]
            resolved[direction] = keys
        return resolved

    def _palette(self, spec: GameSpec) -> dict[str, Any]:
        theme = spec.theme.lower()
        if "space" in theme:
            page_bg = "#08111f"
            panel_bg = "rgba(9, 18, 32, 0.88)"
            panel_border = "#22456d"
            text_main = "#f8fafc"
            text_muted = "#bfd8ff"
            accent = "#7dd3fc"
            player = "#93c5fd"
            hazard = "#fb7185"
            collectible = "#fde68a"
            background_start = "#091325"
            background_end = "#02060d"
            grid = "rgba(125, 211, 252, 0.11)"
        elif "zombie" in theme:
            page_bg = "#10150d"
            panel_bg = "rgba(18, 25, 13, 0.88)"
            panel_border = "#3d5324"
            text_main = "#f8fafc"
            text_muted = "#d9f99d"
            accent = "#bef264"
            player = "#fde68a"
            hazard = "#86efac"
            collectible = "#fca5a5"
            background_start = "#18240f"
            background_end = "#060905"
            grid = "rgba(190, 242, 100, 0.09)"
        else:
            page_bg = "#101726"
            panel_bg = "rgba(14, 21, 35, 0.88)"
            panel_border = "#31435c"
            text_main = "#f8fafc"
            text_muted = "#cbd5e1"
            accent = "#fbbf24"
            player = "#38bdf8"
            hazard = "#f87171"
            collectible = "#34d399"
            background_start = "#0f172a"
            background_end = "#020617"
            grid = "rgba(248, 250, 252, 0.08)"
        return {
            "css": {
                "page_bg": page_bg,
                "panel_bg": panel_bg,
                "panel_border": panel_border,
                "text_main": text_main,
                "text_muted": text_muted,
                "accent": accent,
            },
            "js": {
                "player": player,
                "hazard": hazard,
                "collectible": collectible,
                "backgroundStart": background_start,
                "backgroundEnd": background_end,
                "grid": grid,
            },
        }
