"""Switch platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BIT_CLOSE_TAPS_ON_SENSOR_LOST,
    BIT_DUAL_ZONE_MODE,
    BIT_FLOOR_WASHING_MODE,
    BIT_KEYPAD_LOCKS,
    BIT_WIRELESS_PAIRING,
    BIT_ZONE_1,
    BIT_ZONE_2,
    COORDINATOR,
    DOMAIN,
    MASK_ZONE_BOTH,
)
from .coordinator import clear_bits, set_bits, toggle_zone_1_off, toggle_zone_1_on
from .entity import NeptunSmartEntity


@dataclass(frozen=True, kw_only=True)
class NeptunSwitchDescription(SwitchEntityDescription):
    """Describe Neptun Smart switch."""

    is_on_fn: Callable[[int], bool]
    turn_on_fn: Callable[[int], int]
    turn_off_fn: Callable[[int], int]
    available_fn: Callable[[int], bool] | None = None


BASE_DESCRIPTIONS: tuple[NeptunSwitchDescription, ...] = (
    NeptunSwitchDescription(
        key="zona_1_switch",
        name="Zona 1 Switch",
        icon="mdi:water-pump",
        is_on_fn=lambda value: bool(value & BIT_ZONE_1),
        turn_on_fn=toggle_zone_1_on,
        turn_off_fn=toggle_zone_1_off,
    ),
    NeptunSwitchDescription(
        key="zona_2_switch",
        name="Zona 2 Switch",
        icon="mdi:water-pump",
        is_on_fn=lambda value: bool(value & BIT_ZONE_2),
        turn_on_fn=lambda value: set_bits(value, BIT_ZONE_2),
        turn_off_fn=lambda value: clear_bits(value, BIT_ZONE_2),
        available_fn=lambda value: bool(value & BIT_DUAL_ZONE_MODE),
    ),
    NeptunSwitchDescription(
        key="zona_1_2_switch",
        name="Zona 1 + Zona 2 Switch",
        icon="mdi:valve",
        is_on_fn=lambda value: bool((value & MASK_ZONE_BOTH) == MASK_ZONE_BOTH),
        turn_on_fn=lambda value: set_bits(value, MASK_ZONE_BOTH),
        turn_off_fn=lambda value: clear_bits(value, MASK_ZONE_BOTH),
    ),
    NeptunSwitchDescription(
        key="dual_zone_mode_switch",
        name="Dual Zone Mode Switch",
        icon="mdi:tally-mark-2",
        is_on_fn=lambda value: bool(value & BIT_DUAL_ZONE_MODE),
        turn_on_fn=lambda value: set_bits(value, BIT_DUAL_ZONE_MODE),
        turn_off_fn=lambda value: clear_bits(value, BIT_DUAL_ZONE_MODE),
    ),
    NeptunSwitchDescription(
        key="floor_washing_mode_switch",
        name="Floor Washing Mode Switch",
        icon="mdi:shower",
        is_on_fn=lambda value: bool(value & BIT_FLOOR_WASHING_MODE),
        turn_on_fn=lambda value: set_bits(value, BIT_FLOOR_WASHING_MODE),
        turn_off_fn=lambda value: clear_bits(value, BIT_FLOOR_WASHING_MODE),
    ),
    NeptunSwitchDescription(
        key="keypad_locks_switch",
        name="Keypad Locks Switch",
        icon="mdi:keyboard",
        is_on_fn=lambda value: bool(value & BIT_KEYPAD_LOCKS),
        turn_on_fn=lambda value: set_bits(value, BIT_KEYPAD_LOCKS),
        turn_off_fn=lambda value: clear_bits(value, BIT_KEYPAD_LOCKS),
    ),
    NeptunSwitchDescription(
        key="closing_taps_on_sensor_lost_switch",
        name="Closing Taps on Sensor Lost",
        icon="mdi:water-off",
        is_on_fn=lambda value: bool(value & BIT_CLOSE_TAPS_ON_SENSOR_LOST),
        turn_on_fn=lambda value: set_bits(value, BIT_CLOSE_TAPS_ON_SENSOR_LOST),
        turn_off_fn=lambda value: clear_bits(value, BIT_CLOSE_TAPS_ON_SENSOR_LOST),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart switches from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    descriptions = list(BASE_DESCRIPTIONS)
    descriptions.append(
        NeptunSwitchDescription(
            key="add_new_sensor_switch",
            name="Add New Sensor",
            icon="mdi:wifi-plus",
            is_on_fn=lambda value: bool(value & BIT_WIRELESS_PAIRING),
            turn_on_fn=lambda value: set_bits(value, BIT_WIRELESS_PAIRING),
            turn_off_fn=lambda value: clear_bits(value, BIT_WIRELESS_PAIRING),
        )
    )
    async_add_entities(
        [NeptunSmartSwitch(coordinator, entry, description) for description in descriptions]
    )


class NeptunSmartSwitch(NeptunSmartEntity, SwitchEntity):
    """Representation of Neptun Smart switch."""

    entity_description: NeptunSwitchDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: NeptunSwitchDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description

    @property
    def _alarm_mode_value(self) -> int:
        return int(self.coordinator.data.get("alarm_mode_raw", 0))

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        return self.entity_description.is_on_fn(self._alarm_mode_value)

    @property
    def available(self) -> bool:
        """Return whether switch is available."""
        base = super().available
        if not base:
            return False

        if self.entity_description.available_fn is None:
            return True
        return self.entity_description.available_fn(self._alarm_mode_value)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        await self.coordinator.async_write_alarm_mode(self.entity_description.turn_on_fn)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        await self.coordinator.async_write_alarm_mode(self.entity_description.turn_off_fn)
