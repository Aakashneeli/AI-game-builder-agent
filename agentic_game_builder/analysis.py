from __future__ import annotations

import re
from dataclasses import dataclass


SUPPORTED_PERSPECTIVES = ("top-down", "side-view", "static-screen")


@dataclass(slots=True)
class PromptSignals:
    theme: str | None
    core_mechanic: str | None
    perspective: str | None
    controls: dict[str, str] | None
    difficulty: str
    duration_seconds: int | None
    score_target: int | None
    lose_condition: str | None
    unsupported_features: list[str]
    tone: str | None
    player_role: str | None
    special_mechanic: str | None
    progression_hint: str | None


THEME_KEYWORDS = {
    "space": {"space", "galaxy", "asteroid", "alien", "ship", "spaceship"},
    "zombie": {"zombie", "undead", "apocalypse"},
    "dungeon": {"dungeon", "cave", "maze", "castle"},
    "ocean": {"ocean", "sea", "submarine", "pirate", "fish"},
    "jungle": {"jungle", "forest", "temple"},
    "cyber": {"cyber", "neon", "robot", "android", "heist", "vault", "drone"},
    "sports": {"soccer", "football", "basketball", "sports"},
    "traffic": {"traffic", "road", "lane", "highway", "car", "crossing"},
}

MECHANIC_KEYWORDS = {
    "collect": {"collect", "collecting", "gather", "pickup", "pick up", "grab", "harvest", "steal", "retrieve"},
    "dodge": {"dodge", "dodging", "avoid", "avoiding", "evade", "escape", "cross", "crossing", "outrun"},
    "survive": {"survive", "surviving", "survival", "last", "endure", "hold out"},
    "hybrid": {"chase", "hunt", "rescue", "heist", "infiltrate"},
}

PERSPECTIVE_KEYWORDS = {
    "top-down": {"top-down", "top down", "overhead"},
    "side-view": {"side-view", "side view", "platformer", "side scrolling"},
    "static-screen": {"static-screen", "static screen", "single screen", "arena"},
}

UNSUPPORTED_KEYWORDS = {
    "multiplayer": {"multiplayer", "co-op", "coop", "online", "pvp"},
    "3d": {"3d", "first-person", "open world"},
    "narrative": {"story", "dialogue tree", "visual novel"},
    "assets": {"voice acting", "cutscene", "cinematic", "realistic graphics"},
}

TONE_KEYWORDS = {
    "cozy": {"cozy", "relaxing", "gentle", "calm", "peaceful", "wholesome"},
    "tense": {"tense", "intense", "dangerous", "survival", "grim", "stressful"},
    "mysterious": {"mystery", "mysterious", "spooky", "haunted", "ancient", "eerie"},
    "playful": {"playful", "cute", "lighthearted", "bouncy", "colorful", "arcade"},
    "chaotic": {"chaotic", "wild", "mayhem", "hectic", "fast-paced", "fast paced"},
}

SPECIAL_MECHANIC_KEYWORDS = {
    "dash": {"dash", "boost", "burst", "sprint"},
    "shield": {"shield", "barrier", "guard", "protect"},
    "magnet": {"magnet", "vacuum", "tractor beam", "pull in"},
    "blink": {"blink", "teleport", "warp"},
    "double jump": {"double jump", "double-jump", "air jump", "extra jump"},
}

PROGRESSION_KEYWORDS = {
    "waves": {"wave", "waves", "rounds", "bursts", "surges", "spikes"},
    "finale": {"boss", "finale", "final phase", "showdown"},
    "ramp": {"ramp", "escalate", "escalating", "gets harder", "endless", "increasing", "survive longer", "intensifying", "building"},
    "steady": {"steady", "gentle", "calm", "casual", "measured"},
}


def analyze_prompt(prompt: str) -> PromptSignals:
    lower_prompt = prompt.lower()
    return PromptSignals(
        theme=infer_theme(lower_prompt),
        core_mechanic=infer_mechanic(lower_prompt),
        perspective=infer_perspective(lower_prompt),
        controls=infer_controls(lower_prompt),
        difficulty=infer_difficulty(lower_prompt),
        duration_seconds=parse_duration_seconds(lower_prompt),
        score_target=parse_score_target(lower_prompt),
        lose_condition=infer_lose_condition(lower_prompt),
        unsupported_features=infer_unsupported_features(lower_prompt),
        tone=infer_tone(lower_prompt),
        player_role=infer_player_role(lower_prompt),
        special_mechanic=infer_special_mechanic(lower_prompt),
        progression_hint=infer_progression_hint(lower_prompt),
    )


def infer_theme(lower_prompt: str) -> str | None:
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return theme
    return None


def infer_mechanic(lower_prompt: str) -> str | None:
    has_collect = any(keyword in lower_prompt for keyword in MECHANIC_KEYWORDS["collect"])
    has_dodge = any(keyword in lower_prompt for keyword in MECHANIC_KEYWORDS["dodge"])
    has_survive = any(keyword in lower_prompt for keyword in MECHANIC_KEYWORDS["survive"])
    if (has_collect and has_dodge) or (has_collect and has_survive):
        return "hybrid"
    if any(word in lower_prompt for word in ("runner", "gauntlet", "obstacle course")) and has_dodge:
        return "dodge"
    for mechanic, keywords in MECHANIC_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return mechanic
    if any(word in lower_prompt for word in ("shooter", "fight", "battle", "runner")):
        return "survive"
    return None


def infer_perspective(lower_prompt: str) -> str | None:
    for perspective, keywords in PERSPECTIVE_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return perspective
    return None


def infer_controls(lower_prompt: str) -> dict[str, str] | None:
    if "mouse" in lower_prompt:
        return {
            "up": "Move mouse up",
            "down": "Move mouse down",
            "left": "Move mouse left",
            "right": "Move mouse right",
        }
    if "wasd" in lower_prompt:
        return {
            "up": "W",
            "down": "S",
            "left": "A",
            "right": "D",
        }
    if "arrow" in lower_prompt:
        return {
            "up": "ArrowUp",
            "down": "ArrowDown",
            "left": "ArrowLeft",
            "right": "ArrowRight",
        }
    return None


def infer_difficulty(lower_prompt: str) -> str:
    if any(word in lower_prompt for word in ("hard", "intense", "brutal")):
        return "hard"
    if any(word in lower_prompt for word in ("easy", "casual", "simple")):
        return "easy"
    return "medium"


def parse_duration_seconds(lower_prompt: str) -> int | None:
    second_match = re.search(r"(\d+)\s*seconds?", lower_prompt)
    if second_match:
        return int(second_match.group(1))
    minute_match = re.search(r"(\d+)\s*minutes?", lower_prompt)
    if minute_match:
        return int(minute_match.group(1)) * 60
    return None


def parse_score_target(lower_prompt: str) -> int | None:
    target_match = re.search(r"(\d+)\s*(points?|stars?|coins?|items?)", lower_prompt)
    if target_match:
        return int(target_match.group(1))
    return None


def infer_lose_condition(lower_prompt: str) -> str | None:
    explicit_failure = re.search(r"(?:lose|fail|fails|game over)\s+if\s+([^.!,;]+)", lower_prompt)
    if explicit_failure:
        condition = _sentence_case(explicit_failure.group(1).strip())
        return f"Lose if {condition}."
    if "one hit" in lower_prompt or "single hit" in lower_prompt:
        return "Lose immediately on contact with a hazard."
    if any(word in lower_prompt for word in ("timer runs out", "time limit", "before time runs out")):
        return "Lose if the timer runs out before the objective is complete."
    if any(word in lower_prompt for word in ("avoid", "dodge", "survive")):
        return "Lose on contact with a hazard."
    return None


def infer_unsupported_features(lower_prompt: str) -> list[str]:
    found: list[str] = []
    for label, keywords in UNSUPPORTED_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            found.append(label)
    return found


def infer_tone(lower_prompt: str) -> str | None:
    for tone, keywords in TONE_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return tone
    return None


def infer_player_role(lower_prompt: str) -> str | None:
    patterns = (
        r"play as\s+(?:(?:a|an|the)\s+)?([a-z][a-z\s-]+)",
        r"you are\s+(?:(?:a|an|the)\s+)?([a-z][a-z\s-]+)",
        r"control\s+(?:(?:a|an|the)\s+)?([a-z][a-z\s-]+)",
        r"player is\s+(?:(?:a|an|the)\s+)?([a-z][a-z\s-]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, lower_prompt)
        if not match:
            continue
        role = re.split(r"\b(?:who|that|in|on|with|and|while|where|to|for|through|across|inside|using)\b", match.group(1), maxsplit=1)[0]
        words = re.findall(r"[a-z]+", role)
        if words:
            return " ".join(words[:4])
    return None


def infer_special_mechanic(lower_prompt: str) -> str | None:
    for label, keywords in SPECIAL_MECHANIC_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return label
    return None


def infer_progression_hint(lower_prompt: str) -> str | None:
    for label, keywords in PROGRESSION_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return label
    return None


def extract_location_phrase(prompt: str) -> str | None:
    lower_prompt = prompt.lower()
    match = re.search(
        r"(?:in|inside|through|across|around|within|into)\s+(?:a|an|the)?\s*([a-z][a-z\s-]+?)(?:\b(?:with|while|where|that|who|using|and)\b|[,.]|$)",
        lower_prompt,
    )
    if not match:
        return None
    return clean_fragment(match.group(1))


def extract_focus_terms(prompt: str, limit: int = 6) -> list[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "browser",
        "build",
        "create",
        "for",
        "game",
        "idea",
        "make",
        "me",
        "simple",
        "small",
        "the",
        "that",
        "this",
        "where",
        "with",
        "you",
    }
    words = [word.lower() for word in re.findall(r"[A-Za-z]+", prompt)]
    return [word for word in words if len(word) > 2 and word not in stopwords][:limit]


def extract_object_after_keywords(prompt: str, keywords: tuple[str, ...]) -> str | None:
    lower_prompt = prompt.lower()
    joined = "|".join(re.escape(keyword) for keyword in keywords)
    match = re.search(
        rf"(?:{joined})\s+(?:a|an|the)?\s*([a-z][a-z\s-]+?)(?:\b(?:and|while|with|through|across|in|on|to|for)\b|[,.]|$)",
        lower_prompt,
    )
    if not match:
        return None
    return clean_fragment(match.group(1))


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-") or "generated-game"


def prettify_theme(theme: str | None) -> str:
    if not theme:
        return "arcade"
    mapping = {
        "space": "space",
        "zombie": "zombie outbreak",
        "dungeon": "dungeon crawl",
        "ocean": "ocean",
        "jungle": "jungle",
        "cyber": "cyber arena",
        "sports": "sports arena",
        "traffic": "city traffic",
    }
    return mapping.get(theme, theme)


def clean_fragment(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return cleaned
    return cleaned.strip(" .,!?:;")


def _sentence_case(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        return cleaned
    return cleaned[0].lower() + cleaned[1:]
