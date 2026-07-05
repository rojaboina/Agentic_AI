from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.db import connect, initialize_database


@dataclass(frozen=True)
class ModuleIntent:
    module: str
    intent_text: str
    positive_signals: str
    avoid_signals: str


MODULE_GUIDANCE = {
    "autobiography_memoir": {
        "focus": "reflective autobiography or memoir",
        "positive": "emotional depth; resilience; mortality; meaning; service; transformation; medical, spiritual, creative, or adversity-driven life stories",
        "avoid": "celebrity memoirs that are mostly fame-driven; memoirs without introspection or craft",
    },
    "self_help_personal_growth": {
        "focus": "self-help or personal growth book",
        "positive": "practical wisdom; healing; mindset; compassion; purpose; communication; focus; financial freedom; spiritually open but useful guidance",
        "avoid": "generic motivation; overly aggressive productivity; shallow advice without depth",
    },
    "technical": {
        "focus": "technical book",
        "positive": "data engineering; distributed systems; AI orchestration; applied ML systems; system design; durable engineering concepts; practical architecture",
        "avoid": "shallow AI hype; overly academic material without clear building value",
    },
    "poetry_reflective_writing": {
        "focus": "poetry or reflective writing book",
        "positive": "accessible poetry; prose poetry; illustrated philosophy; healing reflections; tenderness; identity; resilience; self-trust; grief; hope",
        "avoid": "extremely dense or obscure poetry as the default recommendation",
    },
    "philosophy": {
        "focus": "readable practical philosophy book",
        "positive": "meaning; ethics; suffering; freedom; attention; purpose; existential thought; Stoic ideas; contemplative daily-life philosophy",
        "avoid": "very technical academic philosophy; abstract argument-heavy texts without context",
    },
    "spirituality": {
        "focus": "spirituality book",
        "positive": "spiritual growth; healing; forgiveness; consciousness; manifestation with depth; prayer; meditation; mystical experience; warm reflective spiritual memoirs",
        "avoid": "highly dogmatic books unless requested; shallow manifestation books that repeat ideas without new depth",
    },
}


def generate_recommendation_intents(settings: Settings) -> list[ModuleIntent]:
    initialize_database(settings)
    taste_profile = load_taste_profile(settings)
    modules = load_enabled_modules(settings)
    intents = [build_intent(module, description, notes, taste_profile) for module, description, notes in modules]
    save_intents(settings, intents)
    return intents


def load_enabled_modules(settings: Settings) -> list[tuple[str, str, str | None]]:
    with connect(settings) as conn:
        rows = conn.execute(
            """
            SELECT module, description, notes
            FROM recommendation_modules
            WHERE weekly_enabled = 1
            ORDER BY module
            """
        ).fetchall()
    return [(row["module"], row["description"], row["notes"]) for row in rows]


def load_taste_profile(settings: Settings) -> str:
    path = taste_profile_path(settings)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def taste_profile_path(settings: Settings) -> Path:
    return settings.project_root / "docs" / "taste_profile.md"


def build_intent(
    module: str,
    description: str,
    module_notes: str | None,
    taste_profile: str,
) -> ModuleIntent:
    guidance = MODULE_GUIDANCE.get(module, {})
    focus = guidance.get("focus", description)
    positive = guidance.get("positive", description)
    avoid = guidance.get("avoid", module_notes or "")
    global_signals = compact_global_signals(taste_profile)

    intent_text = (
        f"Find one {focus} for Roja's weekly book recommendations. "
        f"Prioritize books that match these taste signals: {positive}. "
        f"Also consider the broader reading profile: {global_signals}. "
        f"Exclude books already read, rejected, or recently recommended. "
        f"Avoid: {avoid}. "
        "Prefer a book with a clear author, concise summary, trustworthy source, and Goodreads rating when available."
    )
    return ModuleIntent(
        module=module,
        intent_text=single_line(intent_text),
        positive_signals=positive,
        avoid_signals=avoid,
    )


def compact_global_signals(taste_profile: str) -> str:
    signals = []
    capture = False
    for line in taste_profile.splitlines():
        stripped = line.strip()
        if stripped == "## Strong Signals":
            capture = True
            continue
        if capture and stripped.startswith("## "):
            break
        if capture and stripped.startswith("- "):
            signals.append(stripped[2:])
    return "; ".join(signals[:6]) or "meaning, healing, practical wisdom, technical depth, reflective writing"


def save_intents(settings: Settings, intents: list[ModuleIntent]) -> None:
    profile_path = str(taste_profile_path(settings))
    with connect(settings) as conn:
        for intent in intents:
            conn.execute(
                """
                INSERT INTO recommendation_intents (
                    module, intent_text, positive_signals, avoid_signals, source_profile_path, active
                )
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(module) DO UPDATE SET
                    intent_text = excluded.intent_text,
                    positive_signals = excluded.positive_signals,
                    avoid_signals = excluded.avoid_signals,
                    source_profile_path = excluded.source_profile_path,
                    active = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    intent.module,
                    intent.intent_text,
                    intent.positive_signals,
                    intent.avoid_signals,
                    profile_path,
                ),
            )


def single_line(value: str) -> str:
    return " ".join(value.split())

