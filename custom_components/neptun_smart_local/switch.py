"""Switch platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS,
    BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS,
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
    translation_placeholders: dict[str, str] | None = None


BASE_DESCRIPTIONS: tuple[NeptunSwitchDescription, ...] = (
    NeptunSwitchDescription(
        key="zona_1_switch",
        translation_key="zone_1",
        icon="mdi:water-pump",
        is_on_fn=lambda value: bool(value & BIT_ZONE_1),
        turn_on_fn=toggle_zone_1_on,
        turn_off_fn=toggle_zone_1_off,
    ),
    NeptunSwitchDescription(
        key="zona_2_switch",
        translation_key="zone_2",
        icon="mdi:water-pump",
        is_on_fn=lambda value: bool(value & BIT_ZONE_2),
        turn_on_fn=lambda value: set_bits(value, BIT_ZONE_2),
        turn_off_fn=lambda value: clear_bits(value, BIT_ZONE_2),
        available_fn=lambda value: bool(value & BIT_DUAL_ZONE_MODE),
    ),
    NeptunSwitchDescription(
        key="zona_1_2_switch",
        translation_key="zone_1_2",
        icon="mdi:valve",
        is_on_fn=lambda value: bool((value & MASK_ZONE_BOTH) == MASK_ZONE_BOTH),
        turn_on_fn=lambda value: set_bits(value, MASK_ZONE_BOTH),
        turn_off_fn=lambda value: clear_bits(value, MASK_ZONE_BOTH),
    ),
    NeptunSwitchDescription(
        key="dual_zone_mode_switch",
        translation_key="dual_zone_mode",
        icon="mdi:tally-mark-2",
        is_on_fn=lambda value: bool(value & BIT_DUAL_ZONE_MODE),
        turn_on_fn=lambda value: set_bits(value, BIT_DUAL_ZONE_MODE),
        turn_off_fn=lambda value: clear_bits(value, BIT_DUAL_ZONE_MODE),
    ),
    NeptunSwitchDescription(
        key="floor_washing_mode_switch",
        translation_key="floor_washing_mode",
        icon="mdi:shower",
        is_on_fn=lambda value: bool(value & BIT_FLOOR_WASHING_MODE),
        turn_on_fn=lambda value: set_bits(value, BIT_FLOOR_WASHING_MODE),
        turn_off_fn=lambda value: clear_bits(value, BIT_FLOOR_WASHING_MODE),
    ),
    NeptunSwitchDescription(
        key="keypad_locks_switch",
        translation_key="keypad_locks",
        icon="mdi:keyboard",
        is_on_fn=lambda value: bool(value & BIT_KEYPAD_LOCKS),
        turn_on_fn=lambda value: set_bits(value, BIT_KEYPAD_LOCKS),
        turn_off_fn=lambda value: clear_bits(value, BIT_KEYPAD_LOCKS),
    ),
    NeptunSwitchDescription(
        key="closing_taps_on_sensor_lost_switch",
        translation_key="closing_taps_on_sensor_lost",
        icon="mdi:water-off",
        is_on_fn=lambda value: bool(value & BIT_CLOSE_TAPS_ON_SENSOR_LOST),
        turn_on_fn=lambda value: set_bits(value, BIT_CLOSE_TAPS_ON_SENSOR_LOST),
        turn_off_fn=lambda value: clear_bits(value, BIT_CLOSE_TAPS_ON_SENSOR_LOST),
    ),
    NeptunSwitchDescription(
        key="close_group_1_on_sensor_loss_switch",
        translation_key="close_group_1_on_sensor_loss",
        icon="mdi:valve",
        is_on_fn=lambda value: bool(value & BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS),
        turn_on_fn=lambda value: set_bits(value, BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS),
        turn_off_fn=lambda value: clear_bits(value, BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS),
    ),
    NeptunSwitchDescription(
        key="close_group_2_on_sensor_loss_switch",
        translation_key="close_group_2_on_sensor_loss",
        icon="mdi:valve",
        is_on_fn=lambda value: bool(value & BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS),
        turn_on_fn=lambda value: set_bits(value, BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS),
        turn_off_fn=lambda value: clear_bits(value, BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS),
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
            translation_key="add_new_sensor",
            icon="mdi:wifi-plus",
            is_on_fn=lambda value: bool(value & BIT_WIRELESS_PAIRING),
            turn_on_fn=lambda value: set_bits(value, BIT_WIRELESS_PAIRING),
            turn_off_fn=lambda value: clear_bits(value, BIT_WIRELESS_PAIRING),
        )
    )
    for idx in coordinator.installed_counters:
        descriptions.append(
            NeptunSwitchDescription(
                key=f"counter_{idx}_enabled_switch",
                translation_key="counter_enabled",
                translation_placeholders={"number": str(idx)},
                icon="mdi:counter",
                is_on_fn=lambda value, idx=idx: bool(
                    (coordinator.data or {}).get(f"counter_{idx}_enabled")
                ),
                turn_on_fn=lambda value: value,
                turn_off_fn=lambda value: value,
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
        super().__init__(
            coordinator,
            entry,
            key=description.key,
            name=description.name,
            translation_key=description.translation_key,
            translation_placeholders=description.translation_placeholders,
        )
        self.entity_description = description

    @property
    def _alarm_mode_value(self) -> int:
        return int((self.coordinator.data or {}).get("alarm_mode_raw", 0))

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
        if not self.available:
            name = self.name or self.entity_id or self._key
            raise HomeAssistantError(
                f"{name} is unavailable, command is blocked"
            )
        if self.entity_description.key.endswith("_enabled_switch"):
            idx = int(self.entity_description.key.split("_")[1])
            address = 123 + (idx - 1)
            data_key = f"counter_{idx}_cfg_raw"
            await self.coordinator.async_write_register_transform(
                address=address,
                data_key=data_key,
                transform=lambda current: int(current) | 0x1,
            )
            return
        await self.coordinator.async_write_alarm_mode(self.entity_description.turn_on_fn)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        if not self.available:
            name = self.name or self.entity_id or self._key
            raise HomeAssistantError(
                f"{name} is unavailable, command is blocked"
            )
        if self.entity_description.key.endswith("_enabled_switch"):
            idx = int(self.entity_description.key.split("_")[1])
            address = 123 + (idx - 1)
            data_key = f"counter_{idx}_cfg_raw"
            await self.coordinator.async_write_register_transform(
                address=address,
                data_key=data_key,
                transform=lambda current: int(current) & ~0x1,
            )
            return
        await self.coordinator.async_write_alarm_mode(self.entity_description.turn_off_fn)
