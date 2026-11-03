"""Home Assistant select for Hatch Baby's sound library.

Exposes the already-supported REST Baby audio selection as a native SelectEntity,
so dashboards like Panalume can display an options dropdown without an iframe.
"""

from __future__ import annotations

import re
from typing import Any

from hatch_rest_api import REST_BABY_AUDIO_TRACKS
from homeassistant.components.select import SelectEntity

from .hatch_entity import HatchEntity


# Known app-facing names for the device's internal audio identifiers.
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
    """Convert Hatch enum names into labels without changing their IDs."""
    if raw_name in FRIENDLY_TRACK_NAMES:
        return FRIENDLY_TRACK_NAMES[raw_name]
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw_name).strip()
    if value in ("Brown", "Green", "Grey", "Indigo", "Red"):
        return f"{value} Noise"
    return value


class HatchBabySoundSelect(HatchEntity, SelectEntity):
    """Live sound list. Selecting an option starts the chosen sound."""

    _attr_icon = "mdi:music-note"

    def __init__(self, coordinator: Any, thing_name: str) -> None:
        super().__init__(
            coordinator=coordinator,
            thing_name=thing_name,
            entity_type="Sound",
        )

    def _entries(self) -> dict[str, tuple[str, Any]]:
        """Labels -> ('track' or 'catalog', original ID/name).

        Disambiguate overlapping names rather than hiding one of the tracks.
        """
        entries: dict[str, tuple[str, Any]] = {}
        for track in REST_BABY_AUDIO_TRACKS:
            if track.name == "NONE":
                continue
            label = friendly_track_name(track.name)
            if label in entries:
                label = f"{label} (built-in {track.name})"
            entries[label] = ("track", track)

        sounds = {}  # Hide unverified generic catalog sounds
        for raw_name in sounds:
            label = str(raw_name)
            if label in entries:
                label = f"{label} (Hatch library)"
            if label not in entries:
                entries[label] = ("catalog", raw_name)
        return entries

    @property
    def options(self) -> list[str]:
        return sorted(self._entries(), key=str.casefold)

    @property
    def current_option(self) -> str | None:
        device = self.rest_device
        if device is None or not device.is_playing:
            return None

        entries = self._entries()
        # Preserve the underlying sound ID; a library recording can have a
        # similar name to a built-in recording but a distinct ID.
        for label, (kind, value) in entries.items():
            if kind == "track" and value.value == device.sound_id:
                return label

        sound = (getattr(device, "sounds_by_id", {}) or {}).get(device.sound_id) or {}
        name = sound.get("title")
        if name is not None:
            for label, (kind, value) in entries.items():
                if kind == "catalog" and value == name:
                    return label
        return None

    def select_option(self, option: str) -> None:
        entry = self._entries().get(option)
        if entry is None:
            raise ValueError(f"Unknown Hatch Baby sound: {option}")
        kind, value = entry
        if kind == "track":
            self.rest_device.set_audio_track(value)
        else:
            self.rest_device.set_sound(value)
