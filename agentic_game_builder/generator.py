from __future__ import annotations

import json
from string import Template
from typing import Any

from .models import GameSpec


VANILLA_HTML_TEMPLATE = Template(
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
        <p id="flavorLine" class="flavor-line">${flavor_text}</p>
        <p id="scoreLine">Score: 0</p>
        <p id="statusLine">${objective}</p>
        <p class="framework-chip">Framework: Vanilla JS</p>
      </div>
      <div class="actions">
        <button id="restartButton" type="button">Restart</button>
        <span class="hint">Press R to restart at any time.</span>
      </div>
    </section>
    <div class="game-surface">
      <canvas id="gameCanvas" width="${width}" height="${height}" aria-label="Generated game canvas"></canvas>
    </div>
  </main>
  <script src="game.js"></script>
</body>
</html>
"""
)


PHASER_HTML_TEMPLATE = Template(
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
        <p id="flavorLine" class="flavor-line">${flavor_text}</p>
        <p id="scoreLine">Score: 0</p>
        <p id="statusLine">${objective}</p>
        <p class="framework-chip">Framework: Phaser</p>
      </div>
      <div class="actions">
        <button id="restartButton" type="button">Restart</button>
        <span class="hint">Press R to restart at any time.</span>
      </div>
    </section>
    <div id="gameRoot" class="game-surface" aria-label="Generated Phaser game"></div>
  </main>
  <script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>
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

.flavor-line {
  padding-left: 12px;
  border-left: 3px solid var(--accent);
}

.framework-chip {
  color: var(--accent);
  font-weight: 700;
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

.game-surface {
  width: 100%;
  min-height: 320px;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: #02050b;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  overflow: hidden;
}

canvas,
.game-surface canvas {
  width: 100%;
  height: auto;
  display: block;
}
"""
)


VANILLA_JS_TEMPLATE = """const config = __CONFIG_JSON__;

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreLine = document.getElementById("scoreLine");
const statusLine = document.getElementById("statusLine");
const instructionLine = document.getElementById("instructionLine");
const flavorLine = document.getElementById("flavorLine");
const restartButton = document.getElementById("restartButton");

const state = {
  screen: "running",
  score: 0,
  elapsed: 0,
  lastFrame: 0,
  keys: new Set(),
  mouse: { x: config.width / 2, y: config.height / 2, active: false },
  lastMove: { x: 1, y: 0 },
  dashCooldownUntil: 0,
  player: null,
  hazards: [],
  collectibles: [],
  endMessage: "",
};

function randomRange(min, max) {
  return Math.random() * (max - min) + min;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function randomLaneCenter() {
  return config.laneCenters[Math.floor(Math.random() * config.laneCenters.length)];
}

function makePlayer() {
  if (config.movementModel === "lane_runner") {
    const laneIndex = Math.floor(config.laneCenters.length / 2);
    return {
      x: config.laneCenters[laneIndex],
      y: config.height - 78,
      radius: 18,
      laneIndex,
      targetX: config.laneCenters[laneIndex],
      speed: config.playerSpeed,
      color: config.palette.player,
      vy: 0,
      extraJumps: 0,
    };
  }
  if (config.movementModel === "side_runner") {
    return {
      x: 120,
      y: config.groundY - 18,
      radius: 18,
      speed: config.playerSpeed,
      color: config.palette.player,
      vy: 0,
      onGround: true,
      extraJumps: config.playerAbility === "double_jump" ? 1 : 0,
    };
  }
  return {
    x: config.width / 2,
    y: config.height / 2,
    radius: 16,
    speed: config.playerSpeed,
    color: config.palette.player,
    vy: 0,
    extraJumps: 0,
  };
}

function makeHazard() {
  if (config.hazardBehavior === "fall") {
    return {
      x: randomLaneCenter(),
      y: randomRange(-config.height, -40),
      radius: 20,
      vx: 0,
      vy: randomRange(config.hazardSpeedMin, config.hazardSpeedMax),
      phase: Math.random() * Math.PI * 2,
      color: config.palette.hazard,
    };
  }
  if (config.hazardBehavior === "sweep") {
    return {
      x: config.width + randomRange(40, 360),
      y: config.groundY - 18,
      radius: 20,
      vx: -randomRange(config.hazardSpeedMin, config.hazardSpeedMax),
      vy: 0,
      phase: Math.random() * Math.PI * 2,
      color: config.palette.hazard,
    };
  }
  const speedMultiplier = config.hazardBehavior === "wander" ? 0.65 : 1;
  return {
    x: randomRange(40, config.width - 40),
    y: randomRange(40, config.height - 40),
    radius: 16,
    vx: randomRange(-140, 140) * speedMultiplier,
    vy: randomRange(-140, 140) * speedMultiplier,
    phase: Math.random() * Math.PI * 2,
    color: config.palette.hazard,
  };
}

function makeCollectible() {
  if (config.collectibleBehavior === "fall") {
    return {
      x: randomLaneCenter(),
      y: randomRange(-config.height, -20),
      radius: 12,
      vy: randomRange(150, 210),
      phase: Math.random() * Math.PI * 2,
      color: config.palette.collectible,
    };
  }
  if (config.collectibleBehavior === "hover") {
    return {
      x: randomRange(config.width * 0.35, config.width - 80),
      y: randomRange(config.groundY - 180, config.groundY - 90),
      baseY: 0,
      radius: 12,
      phase: Math.random() * Math.PI * 2,
      color: config.palette.collectible,
    };
  }
  return {
    x: randomRange(40, config.width - 40),
    y: randomRange(40, config.height - 40),
    radius: 11,
    phase: Math.random() * Math.PI * 2,
    driftX: randomRange(-35, 35),
    driftY: randomRange(-35, 35),
    color: config.palette.collectible,
  };
}

function spawnEntities() {
  state.hazards = Array.from({ length: config.hazardCount }, () => makeHazard());
  state.collectibles = Array.from({ length: config.collectibleCount }, () => makeCollectible()).map((collectible) => {
    if (collectible.baseY === 0) {
      collectible.baseY = collectible.y;
    }
    return collectible;
  });
}

function resetGame() {
  state.screen = "running";
  state.score = 0;
  state.elapsed = 0;
  state.lastFrame = 0;
  state.endMessage = "";
  state.lastMove = { x: 1, y: 0 };
  state.dashCooldownUntil = 0;
  state.player = makePlayer();
  spawnEntities();
  render();
}

function circlesOverlap(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y) <= a.radius + b.radius;
}

function endGame(screen, message) {
  state.screen = screen;
  state.endMessage = message;
}

function tryDash() {
  if (config.playerAbility !== "dash" || state.screen !== "running" || state.elapsed < state.dashCooldownUntil) {
    return;
  }

  const distance = config.movementModel === "lane_runner" ? 2 : 120;
  if (config.movementModel === "lane_runner") {
    if (config.controls.left.some((key) => state.keys.has(key))) {
      moveLane(-distance);
    } else if (config.controls.right.some((key) => state.keys.has(key))) {
      moveLane(distance);
    } else {
      moveLane(1);
    }
    state.dashCooldownUntil = state.elapsed + 1.2;
    return;
  }

  let dx = state.lastMove.x;
  let dy = state.lastMove.y;
  if (config.controlMode === "mouse" && state.mouse.active) {
    dx = state.mouse.x - state.player.x;
    dy = state.mouse.y - state.player.y;
  }
  const length = Math.hypot(dx, dy) || 1;
  state.player.x = clamp(state.player.x + (dx / length) * distance, state.player.radius, config.width - state.player.radius);
  state.player.y = clamp(state.player.y + (dy / length) * distance, state.player.radius, config.height - state.player.radius);
  state.dashCooldownUntil = state.elapsed + 1.2;
}

function moveLane(direction) {
  if (config.movementModel !== "lane_runner" || state.screen !== "running") {
    return;
  }
  state.player.laneIndex = clamp(state.player.laneIndex + direction, 0, config.laneCenters.length - 1);
  state.player.targetX = config.laneCenters[state.player.laneIndex];
}

function jumpPlayer() {
  if (config.movementModel !== "side_runner" || state.screen !== "running") {
    return;
  }
  if (state.player.onGround) {
    state.player.vy = -config.jumpStrength;
    state.player.onGround = false;
    return;
  }
  if (config.playerAbility === "double_jump" && state.player.extraJumps > 0) {
    state.player.vy = -config.jumpStrength * 0.92;
    state.player.extraJumps -= 1;
  }
}

function updateTopDownPlayer(dt) {
  if (config.controlMode === "mouse" && state.mouse.active) {
    const dx = state.mouse.x - state.player.x;
    const dy = state.mouse.y - state.player.y;
    const length = Math.hypot(dx, dy);
    if (length > 1) {
      const step = Math.min(length, state.player.speed * dt);
      state.player.x += (dx / length) * step;
      state.player.y += (dy / length) * step;
    }
  } else {
    let dx = 0;
    let dy = 0;
    if (config.controls.left.some((key) => state.keys.has(key))) dx -= 1;
    if (config.controls.right.some((key) => state.keys.has(key))) dx += 1;
    if (config.controls.up.some((key) => state.keys.has(key))) dy -= 1;
    if (config.controls.down.some((key) => state.keys.has(key))) dy += 1;
    const length = Math.hypot(dx, dy) || 1;
    if (dx !== 0 || dy !== 0) {
      state.lastMove = { x: dx / length, y: dy / length };
    }
    state.player.x += (dx / length) * state.player.speed * dt;
    state.player.y += (dy / length) * state.player.speed * dt;
  }
  state.player.x = clamp(state.player.x, state.player.radius, config.width - state.player.radius);
  state.player.y = clamp(state.player.y, state.player.radius, config.height - state.player.radius);
}

function updateLaneRunnerPlayer(dt) {
  const delta = state.player.targetX - state.player.x;
  if (Math.abs(delta) > 2) {
    state.lastMove = { x: Math.sign(delta), y: 0 };
  }
  state.player.x += delta * Math.min(1, dt * 14);
  state.player.x = clamp(state.player.x, config.laneCenters[0], config.laneCenters[config.laneCenters.length - 1]);
  state.player.y = config.height - 78;
}

function updateSideRunnerPlayer(dt) {
  let dx = 0;
  if (config.controls.left.some((key) => state.keys.has(key))) dx -= 1;
  if (config.controls.right.some((key) => state.keys.has(key))) dx += 1;
  if (dx !== 0) {
    state.lastMove = { x: dx, y: 0 };
  }
  state.player.x += dx * state.player.speed * dt;
  state.player.vy += config.gravity * dt;
  state.player.y += state.player.vy * dt;
  if (state.player.y >= config.groundY - state.player.radius) {
    state.player.y = config.groundY - state.player.radius;
    state.player.vy = 0;
    state.player.onGround = true;
    state.player.extraJumps = config.playerAbility === "double_jump" ? 1 : 0;
  }
  state.player.x = clamp(state.player.x, state.player.radius + 20, config.width - state.player.radius - 20);
}

function updatePlayer(dt) {
  if (config.movementModel === "lane_runner") return updateLaneRunnerPlayer(dt);
  if (config.movementModel === "side_runner") return updateSideRunnerPlayer(dt);
  return updateTopDownPlayer(dt);
}

function respawnHazard(hazard) {
  Object.assign(hazard, makeHazard());
}

function respawnCollectible(collectible) {
  const replacement = makeCollectible();
  if (replacement.baseY === 0) replacement.baseY = replacement.y;
  Object.assign(collectible, replacement);
}

function updateHazards(dt) {
  for (const hazard of state.hazards) {
    if (config.hazardBehavior === "seek") {
      const dx = state.player.x - hazard.x;
      const dy = state.player.y - hazard.y;
      const length = Math.hypot(dx, dy) || 1;
      const speed = randomRange(config.hazardSpeedMin * 0.82, config.hazardSpeedMax * 0.82);
      hazard.x += (dx / length) * speed * dt;
      hazard.y += (dy / length) * speed * dt;
      continue;
    }
    if (config.hazardBehavior === "fall") {
      hazard.y += hazard.vy * dt;
      if (hazard.y - hazard.radius > config.height) respawnHazard(hazard);
      continue;
    }
    if (config.hazardBehavior === "sweep") {
      hazard.x += hazard.vx * dt;
      if (hazard.x + hazard.radius < 0) respawnHazard(hazard);
      continue;
    }
    hazard.x += hazard.vx * dt;
    hazard.y += hazard.vy * dt;
    if (hazard.x < hazard.radius || hazard.x > config.width - hazard.radius) {
      hazard.vx *= -1;
      hazard.x = clamp(hazard.x, hazard.radius, config.width - hazard.radius);
    }
    if (hazard.y < hazard.radius || hazard.y > config.height - hazard.radius) {
      hazard.vy *= -1;
      hazard.y = clamp(hazard.y, hazard.radius, config.height - hazard.radius);
    }
  }
}

function updateCollectibles(dt) {
  for (const collectible of state.collectibles) {
    if (config.collectibleBehavior === "drift") {
      collectible.x += Math.cos(state.elapsed + collectible.phase) * collectible.driftX * dt;
      collectible.y += Math.sin(state.elapsed + collectible.phase) * collectible.driftY * dt;
      collectible.x = clamp(collectible.x, collectible.radius, config.width - collectible.radius);
      collectible.y = clamp(collectible.y, collectible.radius, config.height - collectible.radius);
      continue;
    }
    if (config.collectibleBehavior === "pulse") {
      collectible.radius = 10 + Math.abs(Math.sin(state.elapsed * 4 + collectible.phase)) * 4;
      continue;
    }
    if (config.collectibleBehavior === "fall") {
      collectible.y += collectible.vy * dt;
      if (collectible.y - collectible.radius > config.height) respawnCollectible(collectible);
      continue;
    }
    if (config.collectibleBehavior === "hover") {
      collectible.y = collectible.baseY + Math.sin(state.elapsed * 3 + collectible.phase) * 14;
    }
  }
}

function handleHazardCollisions() {
  for (const hazard of state.hazards) {
    if (circlesOverlap(state.player, hazard)) {
      endGame("lose", config.loseCondition);
      return;
    }
  }
}

function handleCollectibleCollisions() {
  state.collectibles = state.collectibles.map((collectible) => {
    if (!circlesOverlap(state.player, collectible)) return collectible;
    state.score += config.scorePerCollectible;
    const replacement = makeCollectible();
    if (replacement.baseY === 0) replacement.baseY = replacement.y;
    return replacement;
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
  if (state.screen !== "running") return;
  state.elapsed += dt;
  updatePlayer(dt);
  updateHazards(dt);
  if (config.collectibleCount > 0) updateCollectibles(dt);
  handleHazardCollisions();
  if (state.screen !== "running") return;
  if (config.collectibleCount > 0) handleCollectibleCollisions();
  checkWinCondition();
}

function drawOpenField() {
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

function drawLanes() {
  ctx.fillStyle = config.palette.road;
  ctx.fillRect(0, 0, config.width, config.height);
  ctx.fillStyle = config.palette.roadShoulder;
  ctx.fillRect(0, 0, 34, config.height);
  ctx.fillRect(config.width - 34, 0, 34, config.height);
  ctx.strokeStyle = config.palette.laneMark;
  ctx.setLineDash([20, 18]);
  ctx.lineWidth = 4;
  for (let index = 1; index < config.laneCenters.length; index += 1) {
    const x = (config.laneCenters[index - 1] + config.laneCenters[index]) / 2;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, config.height);
    ctx.stroke();
  }
  ctx.setLineDash([]);
}

function drawGroundStrip() {
  const sky = ctx.createLinearGradient(0, 0, 0, config.height);
  sky.addColorStop(0, config.palette.skyTop);
  sky.addColorStop(1, config.palette.skyBottom);
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, config.width, config.height);
  ctx.fillStyle = config.palette.hill;
  ctx.beginPath();
  ctx.moveTo(0, config.groundY);
  ctx.quadraticCurveTo(config.width * 0.2, config.groundY - 90, config.width * 0.4, config.groundY);
  ctx.quadraticCurveTo(config.width * 0.6, config.groundY - 80, config.width * 0.8, config.groundY);
  ctx.quadraticCurveTo(config.width * 0.9, config.groundY - 40, config.width, config.groundY);
  ctx.lineTo(config.width, config.height);
  ctx.lineTo(0, config.height);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = config.palette.ground;
  ctx.fillRect(0, config.groundY, config.width, config.height - config.groundY);
}

function drawArena() {
  if (config.arenaLayout === "lanes") return drawLanes();
  if (config.arenaLayout === "ground_strip") return drawGroundStrip();
  return drawOpenField();
}

function drawEntity(entity, role) {
  if (config.arenaLayout === "lanes") {
    ctx.fillStyle = entity.color;
    if (role === "collectible") {
      ctx.save();
      ctx.translate(entity.x, entity.y);
      ctx.rotate(Math.PI / 4);
      ctx.fillRect(-10, -10, 20, 20);
      ctx.restore();
      return;
    }
    ctx.fillRect(entity.x - 20, entity.y - 24, 40, 48);
    return;
  }
  if (config.arenaLayout === "ground_strip") {
    ctx.fillStyle = entity.color;
    if (role === "player") {
      ctx.beginPath();
      ctx.moveTo(entity.x, entity.y - 20);
      ctx.lineTo(entity.x + 18, entity.y + 20);
      ctx.lineTo(entity.x - 18, entity.y + 20);
      ctx.closePath();
      ctx.fill();
      return;
    }
    if (role === "hazard") {
      ctx.fillRect(entity.x - 20, entity.y - 18, 40, 36);
      return;
    }
  }
  ctx.beginPath();
  ctx.arc(entity.x, entity.y, entity.radius, 0, Math.PI * 2);
  ctx.fillStyle = entity.color;
  ctx.fill();
}

function drawOverlay() {
  if (state.screen === "running") return;
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
  const scoreParts = [];
  if (config.scoreTarget !== null) scoreParts.push(`Score: ${state.score} / ${config.scoreTarget}`);
  if (config.survivalSeconds !== null) scoreParts.push(`Time: ${state.elapsed.toFixed(1)} / ${config.survivalSeconds} sec`);
  if (scoreParts.length === 0) scoreParts.push(`Score: ${state.score}`);
  scoreLine.textContent = scoreParts.join(" | ");
  statusLine.textContent = state.screen === "running" ? config.objective : state.endMessage;
  instructionLine.textContent = config.instructionText;
  flavorLine.textContent = config.flavorText;
}

function renderLegend() {
  ctx.textAlign = "left";
  ctx.font = "16px Trebuchet MS";
  ctx.fillStyle = "#dbeafe";
  ctx.fillText(`Mode: ${config.variantLabel}`, 18, 28);
  ctx.fillText(`Player: ${config.playerEntity}`, 18, 50);
  ctx.fillText(`Hazards: ${config.hazardEntity}`, 18, 72);
  ctx.fillText(`Tone: ${config.visualTone}`, 18, 94);
  if (config.collectibleEntity) ctx.fillText(`Collectibles: ${config.collectibleEntity}`, 18, 116);
}

function render() {
  drawArena();
  renderLegend();
  for (const collectible of state.collectibles) drawEntity(collectible, "collectible");
  for (const hazard of state.hazards) drawEntity(hazard, "hazard");
  drawEntity(state.player, "player");
  drawOverlay();
  renderHud();
}

function frame(timestamp) {
  if (!state.lastFrame) state.lastFrame = timestamp;
  const dt = Math.min(0.033, (timestamp - state.lastFrame) / 1000);
  state.lastFrame = timestamp;
  update(dt);
  render();
  window.requestAnimationFrame(frame);
}

window.addEventListener("keydown", (event) => {
  state.keys.add(event.key);
  if (event.key.toLowerCase() === "r") resetGame();
  if (event.key === "Shift" || event.key.toLowerCase() === "e") tryDash();
  if (config.movementModel === "lane_runner") {
    if (config.controls.left.some((key) => key === event.key)) moveLane(-1);
    if (config.controls.right.some((key) => key === event.key)) moveLane(1);
  }
  if ((config.controls.up.some((key) => key === event.key) || event.key === " ") && config.movementModel === "side_runner") {
    jumpPlayer();
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


PHASER_JS_TEMPLATE = """const config = __CONFIG_JSON__;

const scoreLine = document.getElementById("scoreLine");
const statusLine = document.getElementById("statusLine");
const instructionLine = document.getElementById("instructionLine");
const flavorLine = document.getElementById("flavorLine");
const restartButton = document.getElementById("restartButton");

let phaserGame = null;

function randomRange(min, max) {
  return Math.random() * (max - min) + min;
}

function randomLaneCenter() {
  return config.laneCenters[Math.floor(Math.random() * config.laneCenters.length)];
}

class AgenticScene extends Phaser.Scene {
  constructor() {
    super("AgenticScene");
    this.elapsed = 0;
    this.score = 0;
    this.ended = false;
    this.endMessage = "";
    this.laneIndex = Math.floor(config.laneCenters.length / 2);
    this.dashCooldownUntil = 0;
    this.extraJumps = 0;
  }

  create() {
    this.keys = this.input.keyboard.addKeys("UP,DOWN,LEFT,RIGHT,W,A,S,D,SPACE,SHIFT,E");
    this.drawBackdrop();
    this.createWorld();
    this.refreshHud();

    this.input.keyboard.on("keydown-R", () => resetGame());
  }

  drawBackdrop() {
    const graphics = this.add.graphics();
    if (config.arenaLayout === "lanes") {
      graphics.fillStyle(Phaser.Display.Color.HexStringToColor(config.palette.road).color, 1);
      graphics.fillRect(0, 0, config.width, config.height);
      graphics.fillStyle(Phaser.Display.Color.HexStringToColor(config.palette.roadShoulder).color, 1);
      graphics.fillRect(0, 0, 34, config.height);
      graphics.fillRect(config.width - 34, 0, 34, config.height);
      graphics.lineStyle(4, Phaser.Display.Color.HexStringToColor(config.palette.laneMark).color, 1);
      for (let index = 1; index < config.laneCenters.length; index += 1) {
        const x = (config.laneCenters[index - 1] + config.laneCenters[index]) / 2;
        graphics.lineBetween(x, 0, x, config.height);
      }
      return;
    }

    if (config.arenaLayout === "ground_strip") {
      graphics.fillGradientStyle(
        Phaser.Display.Color.HexStringToColor(config.palette.skyTop).color,
        Phaser.Display.Color.HexStringToColor(config.palette.skyTop).color,
        Phaser.Display.Color.HexStringToColor(config.palette.skyBottom).color,
        Phaser.Display.Color.HexStringToColor(config.palette.skyBottom).color,
        1
      );
      graphics.fillRect(0, 0, config.width, config.height);
      graphics.fillStyle(Phaser.Display.Color.HexStringToColor(config.palette.ground).color, 1);
      graphics.fillRect(0, config.groundY, config.width, config.height - config.groundY);
      return;
    }

    graphics.fillGradientStyle(
      Phaser.Display.Color.HexStringToColor(config.palette.backgroundStart).color,
      Phaser.Display.Color.HexStringToColor(config.palette.backgroundStart).color,
      Phaser.Display.Color.HexStringToColor(config.palette.backgroundEnd).color,
      Phaser.Display.Color.HexStringToColor(config.palette.backgroundEnd).color,
      1
    );
    graphics.fillRect(0, 0, config.width, config.height);
  }

  createWorld() {
    this.hazards = [];
    this.collectibles = [];
    this.legendText = this.add.text(18, 18, `Mode: ${config.variantLabel}\\nPlayer: ${config.playerEntity}\\nTone: ${config.visualTone}\\nHazards: ${config.hazardEntity}`, {
      fontFamily: "Trebuchet MS",
      fontSize: "16px",
      color: "#dbeafe",
    });

    if (config.movementModel === "side_runner") {
      this.ground = this.add.rectangle(config.width / 2, config.groundY + (config.height - config.groundY) / 2, config.width, config.height - config.groundY, Phaser.Display.Color.HexStringToColor(config.palette.ground).color);
      this.physics.add.existing(this.ground, true);
      this.player = this.add.triangle(120, config.groundY - 18, 0, 36, 18, 0, 36, 36, Phaser.Display.Color.HexStringToColor(config.palette.player).color);
      this.physics.add.existing(this.player);
      this.player.body.setCollideWorldBounds(true);
      this.physics.add.collider(this.player, this.ground);
      this.extraJumps = config.playerAbility === "double_jump" ? 1 : 0;
    } else if (config.movementModel === "lane_runner") {
      this.player = this.add.rectangle(config.laneCenters[this.laneIndex], config.height - 78, 42, 50, Phaser.Display.Color.HexStringToColor(config.palette.player).color);
      this.physics.add.existing(this.player);
      this.player.body.setAllowGravity(false);
      this.player.body.setImmovable(true);
    } else {
      this.player = this.add.circle(config.width / 2, config.height / 2, 16, Phaser.Display.Color.HexStringToColor(config.palette.player).color);
      this.physics.add.existing(this.player);
      this.player.body.setAllowGravity(false);
      this.player.body.setCollideWorldBounds(true);
    }

    for (let index = 0; index < config.hazardCount; index += 1) {
      this.hazards.push(this.spawnHazard());
    }
    for (let index = 0; index < config.collectibleCount; index += 1) {
      this.collectibles.push(this.spawnCollectible());
    }
  }

  spawnHazard() {
    let sprite;
    if (config.arenaLayout === "lanes" || config.arenaLayout === "ground_strip") {
      sprite = this.add.rectangle(0, 0, 40, 40, Phaser.Display.Color.HexStringToColor(config.palette.hazard).color);
    } else {
      sprite = this.add.circle(0, 0, 16, Phaser.Display.Color.HexStringToColor(config.palette.hazard).color);
    }
    this.physics.add.existing(sprite);
    sprite.body.setAllowGravity(false);
    this.resetHazard(sprite);
    return sprite;
  }

  resetHazard(sprite) {
    sprite.phase = Math.random() * Math.PI * 2;
    if (config.hazardBehavior === "fall") {
      sprite.setPosition(randomLaneCenter(), randomRange(-config.height, -40));
      sprite.body.reset(sprite.x, sprite.y);
      sprite.body.setVelocity(0, randomRange(config.hazardSpeedMin, config.hazardSpeedMax));
      return;
    }
    if (config.hazardBehavior === "sweep") {
      sprite.setPosition(config.width + randomRange(40, 360), config.groundY - 18);
      sprite.body.reset(sprite.x, sprite.y);
      sprite.body.setVelocity(-randomRange(config.hazardSpeedMin, config.hazardSpeedMax), 0);
      return;
    }
    sprite.setPosition(randomRange(40, config.width - 40), randomRange(40, config.height - 40));
    sprite.body.reset(sprite.x, sprite.y);
    sprite.speedX = randomRange(-140, 140) * (config.hazardBehavior === "wander" ? 0.65 : 1);
    sprite.speedY = randomRange(-140, 140) * (config.hazardBehavior === "wander" ? 0.65 : 1);
    sprite.body.setVelocity(sprite.speedX, sprite.speedY);
  }

  spawnCollectible() {
    const sprite = this.add.circle(0, 0, 11, Phaser.Display.Color.HexStringToColor(config.palette.collectible).color);
    this.physics.add.existing(sprite);
    sprite.body.setAllowGravity(false);
    this.resetCollectible(sprite);
    return sprite;
  }

  resetCollectible(sprite) {
    sprite.phase = Math.random() * Math.PI * 2;
    if (config.collectibleBehavior === "fall") {
      sprite.setPosition(randomLaneCenter(), randomRange(-config.height, -20));
      sprite.body.reset(sprite.x, sprite.y);
      sprite.body.setVelocity(0, randomRange(150, 210));
      return;
    }
    if (config.collectibleBehavior === "hover") {
      sprite.setPosition(randomRange(config.width * 0.35, config.width - 80), randomRange(config.groundY - 180, config.groundY - 90));
      sprite.baseY = sprite.y;
      sprite.body.reset(sprite.x, sprite.y);
      sprite.body.setVelocity(0, 0);
      return;
    }
    sprite.setPosition(randomRange(40, config.width - 40), randomRange(40, config.height - 40));
    sprite.body.reset(sprite.x, sprite.y);
    sprite.driftX = randomRange(-35, 35);
    sprite.driftY = randomRange(-35, 35);
  }

  tryDash() {
    if (config.playerAbility !== "dash" || this.ended || this.elapsed < this.dashCooldownUntil) {
      return;
    }

    if (config.movementModel === "lane_runner") {
      if (this.keys.A.isDown || this.keys.LEFT.isDown) {
        this.laneIndex = Math.max(0, this.laneIndex - 1);
      } else if (this.keys.D.isDown || this.keys.RIGHT.isDown) {
        this.laneIndex = Math.min(config.laneCenters.length - 1, this.laneIndex + 1);
      } else {
        this.laneIndex = Math.min(config.laneCenters.length - 1, this.laneIndex + 1);
      }
      this.dashCooldownUntil = this.elapsed + 1.2;
      return;
    }

    if (config.movementModel === "side_runner") {
      const direction = this.player.body.velocity.x < 0 ? -1 : 1;
      this.player.x = Phaser.Math.Clamp(this.player.x + direction * 120, 24, config.width - 24);
      this.player.body.reset(this.player.x, this.player.y);
      this.dashCooldownUntil = this.elapsed + 1.2;
      return;
    }

    const pointer = this.input.activePointer;
    const dx = pointer.worldX - this.player.x;
    const dy = pointer.worldY - this.player.y;
    const length = Math.hypot(dx, dy) || 1;
    this.player.x = Phaser.Math.Clamp(this.player.x + (dx / length) * 120, 20, config.width - 20);
    this.player.y = Phaser.Math.Clamp(this.player.y + (dy / length) * 120, 20, config.height - 20);
    this.player.body.reset(this.player.x, this.player.y);
    this.dashCooldownUntil = this.elapsed + 1.2;
  }

  update(_, deltaMs) {
    if (this.ended) return;
    const delta = Math.min(0.033, deltaMs / 1000);
    this.elapsed += delta;
    if (Phaser.Input.Keyboard.JustDown(this.keys.SHIFT) || Phaser.Input.Keyboard.JustDown(this.keys.E)) {
      this.tryDash();
    }
    this.updatePlayer(delta);
    this.updateHazards(delta);
    this.updateCollectibles(delta);
    this.checkCollisions();
    this.checkWinCondition();
    this.refreshHud();
  }

  updatePlayer(delta) {
    if (config.movementModel === "side_runner") {
      let move = 0;
      if (this.keys.A.isDown || this.keys.LEFT.isDown) move -= 1;
      if (this.keys.D.isDown || this.keys.RIGHT.isDown) move += 1;
      this.player.body.setVelocityX(move * config.playerSpeed);
      const wantsJump = Phaser.Input.Keyboard.JustDown(this.keys.W) || Phaser.Input.Keyboard.JustDown(this.keys.UP) || Phaser.Input.Keyboard.JustDown(this.keys.SPACE);
      if (wantsJump && this.player.body.blocked.down) {
        this.player.body.setVelocityY(-config.jumpStrength);
        return;
      }
      if (wantsJump && config.playerAbility === "double_jump" && this.extraJumps > 0) {
        this.player.body.setVelocityY(-config.jumpStrength * 0.92);
        this.extraJumps -= 1;
      }
      if (this.player.body.blocked.down) {
        this.extraJumps = config.playerAbility === "double_jump" ? 1 : 0;
      }
      return;
    }

    if (config.movementModel === "lane_runner") {
      if (Phaser.Input.Keyboard.JustDown(this.keys.A) || Phaser.Input.Keyboard.JustDown(this.keys.LEFT)) {
        this.laneIndex = Math.max(0, this.laneIndex - 1);
      }
      if (Phaser.Input.Keyboard.JustDown(this.keys.D) || Phaser.Input.Keyboard.JustDown(this.keys.RIGHT)) {
        this.laneIndex = Math.min(config.laneCenters.length - 1, this.laneIndex + 1);
      }
      this.player.x += (config.laneCenters[this.laneIndex] - this.player.x) * Math.min(1, delta * 14);
      this.player.body.reset(this.player.x, this.player.y);
      return;
    }

    let vx = 0;
    let vy = 0;
    if (this.keys.A.isDown || this.keys.LEFT.isDown) vx -= 1;
    if (this.keys.D.isDown || this.keys.RIGHT.isDown) vx += 1;
    if (this.keys.W.isDown || this.keys.UP.isDown) vy -= 1;
    if (this.keys.S.isDown || this.keys.DOWN.isDown) vy += 1;
    const length = Math.hypot(vx, vy) || 1;
    this.player.body.setVelocity((vx / length) * config.playerSpeed, (vy / length) * config.playerSpeed);
  }

  updateHazards(delta) {
    for (const hazard of this.hazards) {
      if (config.hazardBehavior === "seek") {
        const dx = this.player.x - hazard.x;
        const dy = this.player.y - hazard.y;
        const length = Math.hypot(dx, dy) || 1;
        const speed = randomRange(config.hazardSpeedMin * 0.82, config.hazardSpeedMax * 0.82);
        hazard.x += (dx / length) * speed * delta;
        hazard.y += (dy / length) * speed * delta;
        hazard.body.reset(hazard.x, hazard.y);
        continue;
      }

      if (config.hazardBehavior === "fall") {
        if (hazard.y - hazard.height / 2 > config.height) this.resetHazard(hazard);
        continue;
      }

      if (config.hazardBehavior === "sweep") {
        if (hazard.x + hazard.width / 2 < 0) this.resetHazard(hazard);
        continue;
      }

      hazard.body.setVelocity(hazard.speedX, hazard.speedY);
      if (hazard.x < hazard.width / 2 || hazard.x > config.width - hazard.width / 2) {
        hazard.speedX *= -1;
        hazard.body.setVelocity(hazard.speedX, hazard.speedY);
      }
      if (hazard.y < hazard.height / 2 || hazard.y > config.height - hazard.height / 2) {
        hazard.speedY *= -1;
        hazard.body.setVelocity(hazard.speedX, hazard.speedY);
      }
    }
  }

  updateCollectibles(delta) {
    for (const collectible of this.collectibles) {
      if (config.collectibleBehavior === "drift") {
        collectible.x += Math.cos(this.elapsed + collectible.phase) * collectible.driftX * delta;
        collectible.y += Math.sin(this.elapsed + collectible.phase) * collectible.driftY * delta;
        collectible.body.reset(collectible.x, collectible.y);
        continue;
      }
      if (config.collectibleBehavior === "pulse") {
        collectible.setScale(1 + Math.abs(Math.sin(this.elapsed * 4 + collectible.phase)) * 0.3);
        collectible.body.setCircle(11 * collectible.scale);
        continue;
      }
      if (config.collectibleBehavior === "fall") {
        if (collectible.y - collectible.radius > config.height) this.resetCollectible(collectible);
        continue;
      }
      if (config.collectibleBehavior === "hover") {
        collectible.y = collectible.baseY + Math.sin(this.elapsed * 3 + collectible.phase) * 14;
        collectible.body.reset(collectible.x, collectible.y);
      }
    }
  }

  checkCollisions() {
    for (const hazard of this.hazards) {
      if (Phaser.Geom.Intersects.RectangleToRectangle(this.player.getBounds(), hazard.getBounds())) {
        this.endGame("lose", config.loseCondition);
        return;
      }
    }
    for (const collectible of this.collectibles) {
      if (Phaser.Geom.Intersects.RectangleToRectangle(this.player.getBounds(), collectible.getBounds())) {
        this.score += config.scorePerCollectible;
        this.resetCollectible(collectible);
      }
    }
  }

  checkWinCondition() {
    if (config.scoreTarget !== null && this.score >= config.scoreTarget) {
      this.endGame("win", config.winCondition);
      return;
    }
    if (config.survivalSeconds !== null && this.elapsed >= config.survivalSeconds) {
      this.endGame("win", config.winCondition);
    }
  }

  endGame(screen, message) {
    this.ended = true;
    this.endMessage = message;
    this.refreshHud();
    const overlay = this.add.rectangle(config.width / 2, config.height / 2, config.width, config.height, 0x030912, 0.72);
    overlay.setDepth(10);
    this.add.text(config.width / 2, config.height / 2 - 30, screen === "win" ? "You Win" : "Game Over", {
      fontFamily: "Trebuchet MS",
      fontSize: "42px",
      color: "#f8fafc",
    }).setOrigin(0.5).setDepth(11);
    this.add.text(config.width / 2, config.height / 2 + 18, message, {
      fontFamily: "Trebuchet MS",
      fontSize: "20px",
      color: "#f8fafc",
      align: "center",
    }).setOrigin(0.5).setDepth(11);
  }

  refreshHud() {
    const scoreParts = [];
    if (config.scoreTarget !== null) scoreParts.push(`Score: ${this.score} / ${config.scoreTarget}`);
    if (config.survivalSeconds !== null) scoreParts.push(`Time: ${this.elapsed.toFixed(1)} / ${config.survivalSeconds} sec`);
    if (scoreParts.length === 0) scoreParts.push(`Score: ${this.score}`);
    scoreLine.textContent = scoreParts.join(" | ");
    statusLine.textContent = this.ended ? this.endMessage : config.objective;
    instructionLine.textContent = config.instructionText;
    flavorLine.textContent = config.flavorText;
  }
}

function resetGame() {
  if (phaserGame) {
    phaserGame.destroy(true);
  }
  phaserGame = new Phaser.Game({
    type: Phaser.AUTO,
    width: config.width,
    height: config.height,
    parent: "gameRoot",
    backgroundColor: config.palette.backgroundEnd,
    physics: {
      default: "arcade",
      arcade: {
        gravity: { y: config.movementModel === "side_runner" ? config.gravity : 0 },
        debug: false,
      },
    },
    scene: AgenticScene,
  });
}

restartButton.addEventListener("click", resetGame);
window.addEventListener("keydown", (event) => {
  if (event.key.toLowerCase() === "r") resetGame();
});

resetGame();
"""


class CodeGenerator:
    def generate(self, spec: GameSpec) -> dict[str, str]:
        config = self._build_runtime_config(spec)
        instruction_text = self._build_instruction_text(spec)
        flavor_text = self._build_flavor_text(spec)
        html = self._build_html(spec, instruction_text, flavor_text)
        css = CSS_TEMPLATE.substitute(**self._palette(spec)["css"])
        js_template = PHASER_JS_TEMPLATE if spec.framework == "phaser" else VANILLA_JS_TEMPLATE
        js = js_template.replace("__CONFIG_JSON__", json.dumps(config, indent=2))
        return {
            "index.html": html,
            "style.css": css,
            "game.js": js,
        }

    def _build_html(self, spec: GameSpec, instruction_text: str, flavor_text: str) -> str:
        template = PHASER_HTML_TEMPLATE if spec.framework == "phaser" else VANILLA_HTML_TEMPLATE
        return template.substitute(
            title=spec.title,
            summary=spec.concept_summary,
            instruction_text=instruction_text,
            flavor_text=flavor_text,
            objective=spec.objective,
            width=str(spec.arena_width),
            height=str(spec.arena_height),
        )

    def _build_runtime_config(self, spec: GameSpec) -> dict[str, Any]:
        palette = self._palette(spec)["js"]
        return {
            "framework": spec.framework,
            "title": spec.title,
            "width": spec.arena_width,
            "height": spec.arena_height,
            "objective": spec.objective,
            "instructionText": self._build_instruction_text(spec),
            "flavorText": self._build_flavor_text(spec),
            "controlMode": self._control_mode(spec),
            "controls": self._resolve_controls(spec.controls),
            "variant": spec.play_variant,
            "variantLabel": spec.play_variant.replace("_", " "),
            "movementModel": spec.movement_model,
            "hazardBehavior": spec.hazard_behavior,
            "collectibleBehavior": spec.collectible_behavior,
            "arenaLayout": spec.arena_layout,
            "playerEntity": spec.player_entity,
            "playerIdentity": spec.player_identity,
            "hazardEntity": spec.hazard_entity,
            "collectibleEntity": spec.collectible_entity,
            "signatureMechanic": spec.signature_mechanic,
            "progressionStyle": spec.progression_style,
            "visualTone": spec.visual_tone,
            "arenaDetail": spec.arena_detail,
            "playerAbility": spec.player_ability,
            "pressureCurve": spec.pressure_curve,
            "hazardPattern": spec.hazard_pattern,
            "hazardCount": spec.hazard_count,
            "collectibleCount": spec.collectible_count,
            "playerSpeed": spec.player_speed,
            "scoreTarget": spec.score_target,
            "survivalSeconds": spec.survival_seconds,
            "scorePerCollectible": spec.score_per_collectible,
            "winCondition": spec.win_condition,
            "loseCondition": spec.lose_condition,
            "palette": palette,
            "laneCenters": self._lane_centers(spec),
            "groundY": spec.arena_height - 84,
            "jumpStrength": 420,
            "gravity": 980,
            "hazardSpeedMin": self._hazard_speed_range(spec)[0],
            "hazardSpeedMax": self._hazard_speed_range(spec)[1],
        }

    def _build_instruction_text(self, spec: GameSpec) -> str:
        ability_hint = self._ability_hint(spec)
        if spec.movement_model == "lane_runner":
            return (
                f"Use {spec.controls['left']} and {spec.controls['right']} to dodge through lanes.{ability_hint}"
            )
        if spec.movement_model == "side_runner":
            return (
                f"Run with {spec.controls['left']} and {spec.controls['right']}. Jump with {spec.controls['up']} or "
                f"Space.{ability_hint}"
            )
        if self._control_mode(spec) == "mouse":
            return f"Move the mouse inside the arena to steer the player.{ability_hint}"
        return (
            f"Move with {spec.controls['up']} / {spec.controls['left']} / {spec.controls['down']} / "
            f"{spec.controls['right']}.{ability_hint}"
        )

    def _build_flavor_text(self, spec: GameSpec) -> str:
        return (
            f"You play as {spec.player_identity} in {spec.arena_detail}. "
            f"Tone: {spec.visual_tone}. Pace: {spec.progression_style}."
        )

    def _ability_hint(self, spec: GameSpec) -> str:
        if spec.player_ability == "dash":
            return " Press Shift or E to dash."
        if spec.player_ability == "double_jump":
            return " Press jump again in the air for a second jump."
        return ""

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

    def _lane_centers(self, spec: GameSpec) -> list[float]:
        lane_count = 5 if spec.play_variant == "lane_dodger" else 3
        spacing = spec.arena_width / (lane_count + 1)
        return [round(spacing * (index + 1), 2) for index in range(lane_count)]

    def _hazard_speed_range(self, spec: GameSpec) -> tuple[int, int]:
        if spec.play_variant == "lane_dodger":
            base = (240, 380)
        elif spec.play_variant == "side_runner":
            base = (250, 360)
        elif spec.play_variant in {"chase_escape", "collector_escape"}:
            base = (110, 175)
        elif spec.play_variant == "collector_rush":
            base = (85, 140)
        else:
            base = (130, 220)

        if spec.pressure_curve == "ramp":
            return (base[0] + 15, base[1] + 25)
        if spec.pressure_curve == "waves":
            return (base[0] + 10, base[1] + 18)
        if spec.pressure_curve == "finale":
            return (base[0] + 5, base[1] + 30)
        return base

    def _palette(self, spec: GameSpec) -> dict[str, Any]:
        theme = spec.theme.lower()
        if "space" in theme:
            colors = {
                "page_bg": "#08111f",
                "panel_bg": "rgba(9, 18, 32, 0.88)",
                "panel_border": "#22456d",
                "text_main": "#f8fafc",
                "text_muted": "#bfd8ff",
                "accent": "#7dd3fc",
                "player": "#93c5fd",
                "hazard": "#fb7185",
                "collectible": "#fde68a",
                "background_start": "#091325",
                "background_end": "#02060d",
                "grid": "rgba(125, 211, 252, 0.11)",
                "road": "#111827",
                "road_shoulder": "#1f2937",
                "lane_mark": "#f8fafc",
                "sky_top": "#0f172a",
                "sky_bottom": "#1e293b",
                "hill": "#1f3a5f",
                "ground": "#334155",
            }
        elif "zombie" in theme or "jungle" in theme:
            colors = {
                "page_bg": "#10150d",
                "panel_bg": "rgba(18, 25, 13, 0.88)",
                "panel_border": "#3d5324",
                "text_main": "#f8fafc",
                "text_muted": "#d9f99d",
                "accent": "#bef264",
                "player": "#fde68a",
                "hazard": "#86efac",
                "collectible": "#fca5a5",
                "background_start": "#18240f",
                "background_end": "#060905",
                "grid": "rgba(190, 242, 100, 0.09)",
                "road": "#1f2937",
                "road_shoulder": "#111827",
                "lane_mark": "#d9f99d",
                "sky_top": "#1b4332",
                "sky_bottom": "#2d6a4f",
                "hill": "#4f772d",
                "ground": "#6b8f3f",
            }
        elif "sports" in theme or "traffic" in theme:
            colors = {
                "page_bg": "#0f172a",
                "panel_bg": "rgba(10, 18, 42, 0.88)",
                "panel_border": "#1d4ed8",
                "text_main": "#f8fafc",
                "text_muted": "#bfdbfe",
                "accent": "#f59e0b",
                "player": "#38bdf8",
                "hazard": "#f97316",
                "collectible": "#facc15",
                "background_start": "#0b1630",
                "background_end": "#050814",
                "grid": "rgba(191, 219, 254, 0.08)",
                "road": "#0f172a",
                "road_shoulder": "#1e293b",
                "lane_mark": "#facc15",
                "sky_top": "#0f172a",
                "sky_bottom": "#1d4ed8",
                "hill": "#1e40af",
                "ground": "#2563eb",
            }
        else:
            colors = {
                "page_bg": "#101726",
                "panel_bg": "rgba(14, 21, 35, 0.88)",
                "panel_border": "#31435c",
                "text_main": "#f8fafc",
                "text_muted": "#cbd5e1",
                "accent": "#fbbf24",
                "player": "#38bdf8",
                "hazard": "#f87171",
                "collectible": "#34d399",
                "background_start": "#0f172a",
                "background_end": "#020617",
                "grid": "rgba(248, 250, 252, 0.08)",
                "road": "#111827",
                "road_shoulder": "#1f2937",
                "lane_mark": "#f8fafc",
                "sky_top": "#0f172a",
                "sky_bottom": "#334155",
                "hill": "#334155",
                "ground": "#475569",
            }
        colors = self._apply_tone_overrides(colors, spec.visual_tone)
        return {
            "css": {
                "page_bg": colors["page_bg"],
                "panel_bg": colors["panel_bg"],
                "panel_border": colors["panel_border"],
                "text_main": colors["text_main"],
                "text_muted": colors["text_muted"],
                "accent": colors["accent"],
            },
            "js": {
                "accent": colors["accent"],
                "player": colors["player"],
                "hazard": colors["hazard"],
                "collectible": colors["collectible"],
                "backgroundStart": colors["background_start"],
                "backgroundEnd": colors["background_end"],
                "grid": colors["grid"],
                "road": colors["road"],
                "roadShoulder": colors["road_shoulder"],
                "laneMark": colors["lane_mark"],
                "skyTop": colors["sky_top"],
                "skyBottom": colors["sky_bottom"],
                "hill": colors["hill"],
                "ground": colors["ground"],
            },
        }

    def _apply_tone_overrides(self, colors: dict[str, str], visual_tone: str) -> dict[str, str]:
        tone = visual_tone.lower()
        if "cozy" in tone:
            colors.update(
                {
                    "accent": "#fbbf24",
                    "text_muted": "#fde68a",
                    "background_start": "#2b1f16",
                    "background_end": "#120c08",
                }
            )
        elif "mysterious" in tone:
            colors.update(
                {
                    "accent": "#67e8f9",
                    "text_muted": "#bae6fd",
                    "background_start": "#101735",
                    "background_end": "#050816",
                    "grid": "rgba(103, 232, 249, 0.09)",
                }
            )
        elif "playful" in tone:
            colors.update(
                {
                    "accent": "#f472b6",
                    "collectible": "#fef08a",
                    "hazard": "#fb7185",
                }
            )
        elif "chaotic" in tone:
            colors.update(
                {
                    "accent": "#fb7185",
                    "hazard": "#f97316",
                    "background_start": "#2a0f16",
                    "background_end": "#090204",
                }
            )
        return colors
