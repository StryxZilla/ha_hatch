"""Dedicated Hatch Baby actions for dashboards and automations."""

from __future__ import annotations

from hatch_rest_api import RestBaby
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HatchDataUpdateCoordinator
from .const import DOMAIN
from .hatch_entity import HatchEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HatchDataUpdateCoordinator = hass.data[DOMAIN]
    async_add_entities([
        HatchBabyStopSoundButton(coordinator, device.thing_name)
        for device in coordinator.rest_devices
        if isinstance(device, RestBaby)
    ])


class HatchBabyStopSoundButton(HatchEntity, ButtonEntity):
    """Stop the sound using the same API as media_player.media_stop."""

    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator: HatchDataUpdateCoordinator, thing_name: str) -> None:
        super().__init__(
            coordinator=coordinator,
            thing_name=thing_name,
            entity_type="Stop Sound",
        )

    def press(self) -> None:
        self.rest_device.turn_off()
