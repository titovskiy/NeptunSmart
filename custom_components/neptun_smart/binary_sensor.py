"""Binary sensor platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BIT_ALARM_ZONE_1,
    BIT_ALARM_ZONE_2,
    BIT_BATTERY_DRAIN,
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


BASE_BINARY_SENSORS: tuple[NeptunBinarySensorDescription, ...] = (
    NeptunBinarySensorDescription(
        key="floor_washing_mode",
        name="Floor Washing Mode",
        icon="mdi:shower",
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
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_KEYPAD_LOCKS)),
    ),
    NeptunBinarySensorDescription(
        key="dual_zone_mode",
        name="Dual Zone Mode",
        icon="mdi:tally-mark-2",
        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_DUAL_ZONE_MODE)),
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

    for idx in range(1, coordinator.leak_lines + 1):
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

    if coordinator.enable_wireless:
        entities.extend(
            [
                NeptunSmartBinarySensor(
                    coordinator,
                    entry,
                    NeptunBinarySensorDescription(
                        key="battery_drain_wireless_sensors",
                        name="Battery Drain in Wireless Sensors",
                        icon="mdi:battery-alert",
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
                        value_fn=lambda d: bool((d.get("alarm_mode_raw", 0) & BIT_LOST_CONNECTION)),
                    ),
                ),
            ]
        )

        for idx in range(1, coordinator.wireless_sensors + 1):
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

    @property
    def is_on(self) -> bool:
        """Return binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
