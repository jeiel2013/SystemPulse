"""SystemPulse palettes for truecolor and terminals with fewer colors."""

from dataclasses import replace

from textual.theme import Theme

PULSE_DARK = Theme(
    name="pulse-dark",
    primary="#7dd3fc",
    secondary="#93c5fd",
    accent="#38bdf8",
    foreground="#e5e7eb",
    background="#111827",
    surface="#1b293b",
    panel="#172335",
    warning="#fbbf24",
    error="#fb7185",
    success="#4ade80",
    dark=True,
)

PULSE_LIGHT = Theme(
    name="pulse-light",
    primary="#075985",
    secondary="#1d4ed8",
    accent="#0369a1",
    foreground="#172033",
    background="#f4f7fb",
    surface="#ffffff",
    panel="#dce8f3",
    warning="#92400e",
    error="#be123c",
    success="#166534",
    dark=False,
)

# Use colors that survive Rich's 256-color conversion for the main surfaces.
# Otherwise the dark navy background becomes black while its panels become
# bright blue, and the light background loses its separation from white cards.
PULSE_DARK_256 = replace(
    PULSE_DARK,
    foreground="#e4e4e4",
    background="#1c1c1c",
    surface="#262626",
    panel="#303030",
)

PULSE_LIGHT_256 = replace(
    PULSE_LIGHT,
    foreground="#262626",
    background="#eeeeee",
    surface="#ffffff",
    panel="#d7d7d7",
)


def themes_for_color_system(color_system: str | None) -> tuple[Theme, Theme]:
    """Keep surfaces distinct when the terminal cannot show truecolor."""
    if color_system == "truecolor":
        return PULSE_DARK, PULSE_LIGHT
    return PULSE_DARK_256, PULSE_LIGHT_256
