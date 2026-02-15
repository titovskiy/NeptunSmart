"""Select platform for Neptun Smart integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, DOMAIN
from .entity import NeptunSmartEntity

STEP_OPTIONS = ["1", "10", "100"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart selects from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    async_add_entities(
        [NeptunCounterStepSelect(coordinator, entry, idx) for idx in coordinator.installed_counters]
    )


class NeptunCounterStepSelect(NeptunSmartEntity, SelectEntity):
    """Counter module counting step select."""

    _attr_icon = "mdi:counter"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry: ConfigEntry, counter_index: int) -> None:
        super().__init__(
            coordinator,
            entry,
            f"counter_{counter_index}_step",
            f"Counter {counter_index} Step",
        )
        self._counter_index = counter_index
        self._attr_options = STEP_OPTIONS

    @property
    def current_option(self) -> str | None:
        """Return selected step option."""
        value = self.coordinator.data.get(f"counter_{self._counter_index}_step")
        if value is None:
            return None
        option = str(int(value))
        return option if option in STEP_OPTIONS else "1"

    async def async_select_option(self, option: str) -> None:
        """Set counting step."""
        if option not in STEP_OPTIONS:
            return
        await self.coordinator.async_write_counter_step(self._counter_index, int(option))
