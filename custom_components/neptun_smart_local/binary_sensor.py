"""Binary sensor platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BIT_ALARM_ZONE_1,
    BIT_ALARM_ZONE_2,
    BIT_BATTERY_DRAIN,
    BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS,
    BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS,
    BIT_DUAL_ZONE_MODE,
    BIT_FLOOR_WASHING_MODE,
    BIT_KEYPAD_LOCKS,
    BIT_LOST_CONNECTION,
    BIT_ZONE_1,
    BIT_ZONE_2,
    COORDINATOR,
    DOMAIN,
)
from .entity import NeptunSmartEntity


@dataclass(frozen=True, kw_only=True)
class NeptunBinarySensorDescription(BinarySensorEntityDescription):
    """Describe Neptun Smart binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool]
    enabled_default: bool = True
    diagnostic: bool = False


BASE_BINARY_SENSORS: tuple[NeptunBinarySensorDescription, ...] = (
    NeptunBinarySensorDescription(
        key="floor_washing_mode",
        translation_key="floor_washing_mode",
        icon="mdi:shower",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_FLOOR_WASHING_MODE)),
    ),
    NeptunBinarySensorDescription(
        key="alarm_zone_1",
        translation_key="alarm_zone_1",
        icon="mdi:alert",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ALARM_ZONE_1)),
    ),
    NeptunBinarySensorDescription(
        key="alarm_zone_2",
        translation_key="alarm_zone_2",
        icon="mdi:alert",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ALARM_ZONE_2)),
    ),
    NeptunBinarySensorDescription(
        key="zona_1",
        translation_key="zone_1",
        icon="mdi:water-pump",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ZONE_1)),
    ),
    NeptunBinarySensorDescription(
        key="zona_2",
        translation_key="zone_2",
        icon="mdi:water-pump",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ZONE_2)),
    ),
    NeptunBinarySensorDescription(
        key="keypad_locks",
        translation_key="keypad_locks",
        icon="mdi:keyboard",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_KEYPAD_LOCKS)),
    ),
    NeptunBinarySensorDescription(
        key="dual_zone_mode",
        translation_key="dual_zone_mode",
        icon="mdi:tally-mark-2",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_DUAL_ZONE_MODE)),
    ),
    NeptunBinarySensorDescription(
        key="close_group_1_on_sensor_loss",
        translation_key="close_group_1_on_sensor_loss",
        icon="mdi:valve",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS)),
    ),
    NeptunBinarySensorDescription(
        key="close_group_2_on_sensor_loss",
        translation_key="close_group_2_on_sensor_loss",
        icon="mdi:valve",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_CLOSE_GROUP_2_ON_SENSOR_LOSS)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart binary sensors from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    entities: list[BinarySensorEntity] = [
        NeptunSmartBinarySensor(coordinator, entry, desc) for desc in BASE_BINARY_SENSORS
    ]

    for idx in coordinator.detected_leak_lines:
        mask = 1 << (idx - 1)
        entities.append(
            NeptunSmartBinarySensor(
                coordinator,
                entry,
                NeptunBinarySensorDescription(
                    key=f"leak_sensor_{idx}",
                    translation_key="leak_sensor",
                    icon="mdi:water-alert",
                    value_fn=lambda d, mask=mask: bool(d.get("leak_sensor_raw", 0) & mask),
                ),
                translation_placeholders={"number": str(idx)},
            )
        )

    for idx in coordinator.installed_counters:
        entities.append(
            NeptunSmartBinarySensor(
                coordinator,
                entry,
                NeptunBinarySensorDescription(
                    key=f"counter_{idx}_enabled",
                    translation_key="counter_status",
                    icon="mdi:counter",
                    enabled_default=False,
                    diagnostic=True,
                    value_fn=lambda d, idx=idx: bool(d.get(f"counter_{idx}_enabled")),
                ),
                translation_placeholders={"number": str(idx)},
            )
        )

    if coordinator.installed_wireless_sensors:
        entities.extend(
            [
                NeptunSmartBinarySensor(
                    coordinator,
                    entry,
                    NeptunBinarySensorDescription(
                        key="battery_drain_wireless_sensors",
                        translation_key="battery_drain_wireless_sensors",
                        icon="mdi:battery-alert",
                        enabled_default=False,
                        diagnostic=True,
                        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_BATTERY_DRAIN)),
                    ),
                ),
                NeptunSmartBinarySensor(
                    coordinator,
                    entry,
                    NeptunBinarySensorDescription(
                        key="lost_connection_wireless_sensors",
                        translation_key="lost_connection_wireless_sensors",
                        icon="mdi:signal-off",
                        enabled_default=False,
                        diagnostic=True,
                        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_LOST_CONNECTION)),
                    ),
                ),
            ]
        )

        for idx in coordinator.installed_wireless_sensors:
            entities.extend(
                [
                    NeptunSmartBinarySensor(
                        coordinator,
                        entry,
                        NeptunBinarySensorDescription(
                            key=f"wireless_{idx}_alarm",
                            translation_key="wireless_alarm",
                            icon="mdi:alarm",
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_alarm")),
                        ),
                        translation_placeholders={"number": str(idx)},
                    ),
                    NeptunSmartBinarySensor(
                        coordinator,
                        entry,
                        NeptunBinarySensorDescription(
                            key=f"wireless_{idx}_category",
                            translation_key="wireless_category",
                            icon="mdi:check-circle",
                            enabled_default=False,
                            diagnostic=True,
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_category")),
                        ),
                        translation_placeholders={"number": str(idx)},
                    ),
                    NeptunSmartBinarySensor(
                        coordinator,
                        entry,
                        NeptunBinarySensorDescription(
                            key=f"wireless_{idx}_loss",
                            translation_key="wireless_loss",
                            icon="mdi:alert-circle",
                            enabled_default=False,
                            diagnostic=True,
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_loss")),
                        ),
                        translation_placeholders={"number": str(idx)},
                    ),
                ]
            )

    async_add_entities(entities)


class NeptunSmartBinarySensor(NeptunSmartEntity, BinarySensorEntity):
    """Representation of Neptun Smart binary sensor."""

    entity_description: NeptunBinarySensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: NeptunBinarySensorDescription,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
            key=description.key,
            name=description.name,
            translation_key=description.translation_key,
            translation_placeholders=translation_placeholders,
        )
        self.entity_description = description
        self._attr_entity_registry_enabled_default = description.enabled_default
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        """Return binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data or {})
