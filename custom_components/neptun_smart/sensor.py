"""Sensor platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, DOMAIN
from .entity import NeptunSmartEntity


@dataclass(frozen=True, kw_only=True)
class NeptunSensorDescription(SensorEntityDescription):
    """Describe Neptun Smart sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


BASE_SENSORS: tuple[NeptunSensorDescription, ...] = (
    NeptunSensorDescription(
        key="alarm_mode_raw",
        name="Alarm and Mode Raw",
        icon="mdi:code-braces",
        value_fn=lambda d: d.get("alarm_mode_raw"),
    ),
    NeptunSensorDescription(
        key="leak_sensor_raw",
        name="Leak Sensor Raw",
        icon="mdi:water-alert",
        value_fn=lambda d: d.get("leak_sensor_raw"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart sensors from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities: list[SensorEntity] = [NeptunSmartSensor(coordinator, entry, desc) for desc in BASE_SENSORS]

    if coordinator.enable_wireless:
        entities.append(
            NeptunSmartSensor(
                coordinator,
                entry,
                NeptunSensorDescription(
                    key="wireless_sensor_count",
                    name="Connected Wireless Sensors",
                    icon="mdi:wifi",
                    native_unit_of_measurement="pcs",
                    value_fn=lambda d: d.get("wireless_sensor_count"),
                ),
            )
        )

        for idx in range(1, coordinator.wireless_sensors + 1):
            entities.append(
                NeptunSmartSensor(
                    coordinator,
                    entry,
                    NeptunSensorDescription(
                        key=f"wireless_{idx}_raw",
                        name=f"Wireless Sensor {idx} Raw",
                        icon="mdi:chip",
                        value_fn=lambda d, idx=idx: d.get(f"wireless_{idx}_raw"),
                    ),
                )
            )
            entities.append(
                NeptunSmartSensor(
                    coordinator,
                    entry,
                    NeptunSensorDescription(
                        key=f"wireless_{idx}_battery",
                        name=f"Battery Level Sensor {idx}",
                        icon="mdi:battery",
                        device_class=SensorDeviceClass.BATTERY,
                        native_unit_of_measurement=PERCENTAGE,
                        value_fn=lambda d, idx=idx: d.get(f"wireless_{idx}_battery"),
                    ),
                )
            )
            entities.append(
                NeptunSmartSensor(
                    coordinator,
                    entry,
                    NeptunSensorDescription(
                        key=f"wireless_{idx}_signal",
                        name=f"Sensor Signal Level {idx}",
                        icon="mdi:signal",
                        native_unit_of_measurement=PERCENTAGE,
                        value_fn=lambda d, idx=idx: d.get(f"wireless_{idx}_signal"),
                    ),
                )
            )

    for slot in range(1, 5):
        for port in range(1, 3):
            key = f"water_counter_s{slot}_p{port}"
            entities.append(
                NeptunSmartSensor(
                    coordinator,
                    entry,
                    NeptunSensorDescription(
                        key=key,
                        name=f"Water counter S{slot} P{port}",
                        icon="mdi:water",
                        device_class=SensorDeviceClass.WATER,
                        state_class=SensorStateClass.TOTAL_INCREASING,
                        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
                        suggested_display_precision=3,
                        value_fn=lambda d, key=key: d.get(key),
                    ),
                )
            )

    async_add_entities(entities)


class NeptunSmartSensor(NeptunSmartEntity, SensorEntity):
    """Representation of a Neptun Smart sensor."""

    entity_description: NeptunSensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: NeptunSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
