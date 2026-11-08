"""Common entity helpers for Neptun Smart."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NeptunSmartCoordinator


class NeptunSmartEntity(CoordinatorEntity[NeptunSmartCoordinator]):
    """Base entity class for Neptun Smart entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeptunSmartCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str | UndefinedType | None = None,
        translation_key: str | None = None,
        translation_placeholders: dict[str, str] | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        if translation_key is not None:
            self._attr_translation_key = translation_key
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders
        if name is not None and name is not UNDEFINED:
            self._attr_name = name
        self._attr_unique_id = f"{coordinator.unique_prefix}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return metadata for Neptun Smart controller device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.unique_prefix)},
            manufacturer="Neptun",
            model="Smart",
            name=self._entry.title,
            configuration_url=f"http://{self.coordinator.host}",
        )
