"""Number platform for Neptun Smart integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, DOMAIN
from .entity import NeptunSmartEntity


def _counter_water_key(counter_index: int) -> str:
    slot = ((counter_index - 1) // 2) + 1
    port = 1 if counter_index % 2 else 2
    return f"water_counter_s{slot}_p{port}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart numbers from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities: list[NumberEntity] = []
    for idx in coordinator.installed_counters:
        entities.append(NeptunCounterCalibrationNumber(coordinator, entry, idx))

    async_add_entities(entities)


class NeptunCounterCalibrationNumber(NeptunSmartEntity, NumberEntity):
    """Counter current value calibration."""

    _attr_icon = "mdi:gauge"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 2147483.647
    _attr_native_step = 0.001
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_suggested_display_precision = 3
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry: ConfigEntry, counter_index: int) -> None:
        super().__init__(
            coordinator,
            entry,
            f"counter_{counter_index}_calibration",
            f"Counter {counter_index} Calibration",
        )
        self._counter_index = counter_index
        self._water_key = _counter_water_key(counter_index)

    @property
    def native_value(self) -> float | None:
        """Return current counter value."""
        value = self.coordinator.data.get(self._water_key)
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set current counter value."""
        await self.coordinator.async_write_counter_calibration(
            self._counter_index,
            float(value),
        )
