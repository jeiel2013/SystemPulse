"""Two restrained terminal palettes for the same SystemPulse layout."""

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
