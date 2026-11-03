"""Native Home Assistant select for Hatch Baby saved favorite routines."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity

from .hatch_entity import HatchEntity

PROMPT = "Choose a preset..."


class HatchBabyPresetSelect(HatchEntity, SelectEntity):
    """Choose a saved favorite (sound + light settings) on a Hatch Baby."""

    _attr_icon = "mdi:playlist-music"

    def __init__(self, coordinator: Any, thing_name: str) -> None:
        super().__init__(
            coordinator=coordinator,
            thing_name=thing_name,
            entity_type="Preset",
        )

    def _favorites(self) -> dict[str, tuple[str, int]]:
        """Map display labels to (original name, favorite ID).

        Use the same step name and favorite ID as the integration's scene
        entities, including a stable suffix when names repeat.
        """
        device = self.rest_device
        favorites: dict[str, tuple[str, int]] = {}
        if device is None:
            return favorites

        for number, favorite in enumerate(getattr(device, "favorites", []) or [], start=1):
            try:
                name = str(favorite["steps"][0]["name"]).strip()
                favorite_id = int(favorite["id"])
            except (TypeError, KeyError, IndexError, ValueError):
                continue
            if not name:
                continue
            label = name
            if label in favorites or label == PROMPT:
                label = f"{name} (Preset {number})"
            while label in favorites:
                label += " *"
            favorites[label] = (name, favorite_id)
        return favorites

    @property
    def options(self) -> list[str]:
        return [PROMPT, *self._favorites()]

    @property
    def current_option(self) -> str:
        device = self.rest_device
        if device is not None and device.current_playing == "routine":
            current_id = getattr(device, "current_id", None)
            for label, (_, favorite_id) in self._favorites().items():
                if str(current_id) == str(favorite_id):
                    return label
        return PROMPT

    def select_option(self, option: str) -> None:
        if option == PROMPT:
            return  # Display-only placeholder; Stop Sound has its own button.
        entry = self._favorites().get(option)
        if entry is None:
            raise ValueError(f"Unknown Hatch Baby preset: {option}")
        original_name, favorite_id = entry
        # Same API/identifier used by the existing favorite scene entities.
        self.rest_device.set_favorite(f"{original_name}-{favorite_id}")
