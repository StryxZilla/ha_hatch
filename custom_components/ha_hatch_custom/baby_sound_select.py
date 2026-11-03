
"""Home Assistant select for Hatch Baby's sound library.

Exposes Hatch Baby audio selection as a native SelectEntity,
so dashboards like Panalume can display a sound dropdown.
"""

from __future__ import annotations

import re
from typing import Any

from hatch_rest_api import REST_BABY_AUDIO_TRACKS
from homeassistant.components.select import SelectEntity

from .hatch_entity import HatchEntity


PROMPT = "Choose a sound..."


# Friendly names for Hatch Baby's internal audio identifiers.
FRIENDLY_TRACK_NAMES = {
    "AirplaneInt": "Airplane Mode",
    "AnalogNoiseMachine": "Analog Noise Machine",
    "CarInt": "Backseat of the Car",
    "CanalBarge": "French Canal Barge",
    "CaribbeanOcean": "Ocean Waves",
    "CatPurr": "Cat Purring",
    "Fan": "Bedside Fan",
    "Fridge": "Humming Fridge",
    "HatchBlue": "Hatch Navy",
    "PinkNoise": "Pink Noise",
    "PorchRain": "Rain on the Porch",
    "RainClassic": "Rain (Classic)",
    "TentRain": "Rain on Canvas Tent",
    "TrainInt": "Evening Train Ride",
    "White": "White Noise",
    "WombSounds": "Womb Sounds",
}


def friendly_track_name(raw_name: str) -> str:
    """Convert internal sound names into friendly display labels."""

    if raw_name in FRIENDLY_TRACK_NAMES:
        return FRIENDLY_TRACK_NAMES[raw_name]

    value = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        " ",
        raw_name,
    ).strip()

    if value in ("Brown", "Green", "Grey", "Indigo", "Red"):
        return f"{value} Noise"

    return value


class HatchBabySoundSelect(HatchEntity, SelectEntity):
    """Native sound selector for Hatch Baby."""

    _attr_icon = "mdi:music-note"

    def __init__(self, coordinator: Any, thing_name: str) -> None:
        super().__init__(
            coordinator=coordinator,
            thing_name=thing_name,
            entity_type="Sound",
        )

    def _entries(self) -> dict[str, tuple[str, Any]]:
        """Return supported Hatch Baby audio tracks.

        Generic catalog sounds are intentionally excluded because
        some do not work on Hatch Baby devices.
        """

        entries: dict[str, tuple[str, Any]] = {}

        for track in REST_BABY_AUDIO_TRACKS:
            if track.name == "NONE":
                continue

            label = friendly_track_name(track.name)

            if label in entries:
                label = f"{label} (built-in {track.name})"

            entries[label] = ("track", track)

        return entries

    @property
    def options(self) -> list[str]:
        """Show the placeholder first, followed by available sounds."""

        sounds = sorted(
            self._entries(),
            key=str.casefold,
        )

        return [PROMPT, *sounds]

    @property
    def current_option(self) -> str:
        """Return the active sound or the placeholder."""

        device = self.rest_device

        if device is None or not device.is_playing:
            return PROMPT

        entries = self._entries()

        for label, (kind, value) in entries.items():
            if kind == "track" and value.value == device.sound_id:
                return label

        return PROMPT

    def select_option(self, option: str) -> None:
        """Play the selected Hatch Baby sound."""

        if option == PROMPT:
            return

        entry = self._entries().get(option)

        if entry is None:
            raise ValueError(
                f"Unknown Hatch Baby sound: {option}"
            )

        kind, value = entry

        if kind == "track":
            self.rest_device.set_audio_track(value)
        else:
            self.rest_device.set_sound(value)
