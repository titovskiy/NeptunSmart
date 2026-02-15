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
        name="Floor Washing Mode",
        icon="mdi:shower",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_FLOOR_WASHING_MODE)),
    ),
    NeptunBinarySensorDescription(
        key="alarm_zone_1",
        name="Alarm zona 1",
        icon="mdi:alert",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ALARM_ZONE_1)),
    ),
    NeptunBinarySensorDescription(
        key="alarm_zone_2",
        name="Alarm zona 2",
        icon="mdi:alert",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ALARM_ZONE_2)),
    ),
    NeptunBinarySensorDescription(
        key="zona_1",
        name="Zona 1",
        icon="mdi:water-pump",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ZONE_1)),
    ),
    NeptunBinarySensorDescription(
        key="zona_2",
        name="Zona 2",
        icon="mdi:water-pump",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_ZONE_2)),
    ),
    NeptunBinarySensorDescription(
        key="keypad_locks",
        name="Keypad Locks",
        icon="mdi:keyboard",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_KEYPAD_LOCKS)),
    ),
    NeptunBinarySensorDescription(
        key="dual_zone_mode",
        name="Dual Zone Mode",
        icon="mdi:tally-mark-2",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_DUAL_ZONE_MODE)),
    ),
    NeptunBinarySensorDescription(
        key="close_group_1_on_sensor_loss",
        name="Close Group 1 on Sensor Loss",
        icon="mdi:valve",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_CLOSE_GROUP_1_ON_SENSOR_LOSS)),
    ),
    NeptunBinarySensorDescription(
        key="close_group_2_on_sensor_loss",
        name="Close Group 2 on Sensor Loss",
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
                    name=f"LeakSensor {idx}",
                    icon="mdi:water-alert",
                    value_fn=lambda d, mask=mask: bool(d.get("leak_sensor_raw", 0) & mask),
                ),
            )
        )

    for idx in coordinator.installed_counters:
        entities.append(
            NeptunSmartBinarySensor(
                coordinator,
                entry,
                NeptunBinarySensorDescription(
                    key=f"counter_{idx}_enabled",
                    name=f"Counter {idx} Status",
                    icon="mdi:counter",
                    enabled_default=False,
                    diagnostic=True,
                    value_fn=lambda d, idx=idx: bool(d.get(f"counter_{idx}_enabled")),
                ),
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
                        name="Battery Drain in Wireless Sensors",
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
                        name="Lost Connection with Wireless Sensors",
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
                            name=f"Presence of Alarm Sensor {idx}",
                            icon="mdi:alarm",
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_alarm")),
                        ),
                    ),
                    NeptunSmartBinarySensor(
                        coordinator,
                        entry,
                        NeptunBinarySensorDescription(
                            key=f"wireless_{idx}_category",
                            name=f"Availability of Category Sensor {idx}",
                            icon="mdi:check-circle",
                            enabled_default=False,
                            diagnostic=True,
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_category")),
                        ),
                    ),
                    NeptunSmartBinarySensor(
                        coordinator,
                        entry,
                        NeptunBinarySensorDescription(
                            key=f"wireless_{idx}_loss",
                            name=f"Sensor Loss Sensor {idx}",
                            icon="mdi:alert-circle",
                            enabled_default=False,
                            diagnostic=True,
                            value_fn=lambda d, idx=idx: bool(d.get(f"wireless_{idx}_loss")),
                        ),
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
    ) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description
        self._attr_entity_registry_enabled_default = description.enabled_default
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        """Return binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
