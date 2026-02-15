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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, DOMAIN
from .entity import NeptunSmartEntity


@dataclass(frozen=True, kw_only=True)
class NeptunSensorDescription(SensorEntityDescription):
    """Describe Neptun Smart sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    enabled_default: bool = True
    diagnostic: bool = False


BASE_SENSORS: tuple[NeptunSensorDescription, ...] = (
    NeptunSensorDescription(
        key="alarm_mode_raw",
        name="Alarm and Mode Raw",
        icon="mdi:code-braces",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: d.get("alarm_mode_raw"),
    ),
    NeptunSensorDescription(
        key="leak_sensor_raw",
        name="Leak Sensor Raw",
        icon="mdi:water-alert",
        value_fn=lambda d: d.get("leak_sensor_raw"),
    ),
    NeptunSensorDescription(
        key="detected_counters",
        name="Detected Counters",
        icon="mdi:counter",
        native_unit_of_measurement="pcs",
        enabled_default=False,
        diagnostic=True,
        value_fn=lambda d: d.get("detected_counters"),
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

    if coordinator.installed_wireless_sensors:
        entities.append(
            NeptunSmartSensor(
                coordinator,
                entry,
                NeptunSensorDescription(
                    key="wireless_sensor_count",
                    name="Connected Wireless Sensors",
                    icon="mdi:wifi",
                    native_unit_of_measurement="pcs",
                    enabled_default=False,
                    diagnostic=True,
                    value_fn=lambda d: d.get("wireless_sensor_count"),
                ),
            )
        )

        for idx in coordinator.installed_wireless_sensors:
            entities.append(
                NeptunSmartSensor(
                    coordinator,
                    entry,
                    NeptunSensorDescription(
                        key=f"wireless_{idx}_raw",
                        name=f"Wireless Sensor {idx} Raw",
                        icon="mdi:chip",
                        enabled_default=False,
                        diagnostic=True,
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
                        enabled_default=False,
                        diagnostic=True,
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
                        enabled_default=False,
                        diagnostic=True,
                        value_fn=lambda d, idx=idx: d.get(f"wireless_{idx}_signal"),
                    ),
                )
            )

    for counter_idx in coordinator.installed_counters:
        slot = ((counter_idx - 1) // 2) + 1
        port = 1 if counter_idx % 2 else 2
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

    for idx in coordinator.installed_counters:
        entities.append(
            NeptunSmartSensor(
                coordinator,
                entry,
                NeptunSensorDescription(
                    key=f"counter_{idx}_status_code",
                    name=f"Counter {idx} Status Code",
                    icon="mdi:list-status",
                    enabled_default=False,
                    diagnostic=True,
                    value_fn=lambda d, idx=idx: d.get(f"counter_{idx}_status_code"),
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
        self._attr_entity_registry_enabled_default = description.enabled_default
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
