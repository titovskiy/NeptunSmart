"""Select platform for Neptun Smart integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, DOMAIN
from .entity import NeptunSmartEntity

STEP_OPTIONS = {1: "1", 10: "10", 100: "100"}
LINE_TYPE_OPTIONS = {0: "Sensors", 1: "Button"}
GROUP_OPTIONS = {0: "None", 1: "Group 1", 2: "Group 2", 3: "Group 1 + 2"}
CONNECTION_OPTIONS = {0: "Normal", 1: "Namur"}
BAUD_OPTIONS = {
    0x00: "1200",
    0x01: "2400",
    0x02: "4800",
    0x03: "9600",
    0x04: "19200",
    0x05: "38400",
    0x06: "57600",
    0x07: "115200",
    0x08: "230400",
    0x09: "460800",
    0x0A: "921600",
}


@dataclass(frozen=True)
class SelectDesc:
    key: str
    name: str
    options_map: dict[int, str]
    get_code: Callable[[dict], int]
    transform: Callable[[int], Callable[[int], int]]
    address: int
    data_key: str
    icon: str
    entity_category: EntityCategory = EntityCategory.CONFIG


def _mask_transform(shift: int, width: int, value: int) -> Callable[[int], int]:
    mask = ((1 << width) - 1) << shift

    def _apply(current: int) -> int:
        return (int(current) & ~mask) | ((value << shift) & mask)

    return _apply


def _inverse(options_map: dict[int, str]) -> dict[str, int]:
    return {v: k for k, v in options_map.items()}


def _line_type_desc(line: int) -> SelectDesc:
    reg = 1 if line <= 2 else 2
    shift = 10 if line in (1, 3) else 2
    return SelectDesc(
        key=f"line_{line}_type",
        name=f"Line {line} Input Type",
        options_map=LINE_TYPE_OPTIONS,
        get_code=lambda d, line=line: int(d.get(f"line_{line}_type", 0)),
        transform=lambda code, shift=shift: _mask_transform(shift, 2, code),
        address=reg,
        data_key=f"line_cfg_{1 if line <= 2 else 3}_{2 if line <= 2 else 4}_raw",
        icon="mdi:ray-start-end",
    )


def _line_group_desc(line: int) -> SelectDesc:
    reg = 1 if line <= 2 else 2
    shift = 8 if line in (1, 3) else 0
    return SelectDesc(
        key=f"line_{line}_group",
        name=f"Line {line} Valve Group",
        options_map=GROUP_OPTIONS,
        get_code=lambda d, line=line: int(d.get(f"line_{line}_group", 0)),
        transform=lambda code, shift=shift: _mask_transform(shift, 2, code),
        address=reg,
        data_key=f"line_cfg_{1 if line <= 2 else 3}_{2 if line <= 2 else 4}_raw",
        icon="mdi:valve",
    )


def _relay_desc(key: str, name: str, shift: int) -> SelectDesc:
    return SelectDesc(
        key=key,
        name=name,
        options_map=GROUP_OPTIONS,
        get_code=lambda d, shift=shift: int((d.get("relay_cfg_raw", 0) >> shift) & 0x3),
        transform=lambda code, shift=shift: _mask_transform(shift, 2, code),
        address=4,
        data_key="relay_cfg_raw",
        icon="mdi:flash",
    )


def _counter_step_desc(idx: int) -> SelectDesc:
    return SelectDesc(
        key=f"counter_{idx}_step",
        name=f"Counter {idx} Step",
        options_map=STEP_OPTIONS,
        get_code=lambda d, idx=idx: int(d.get(f"counter_{idx}_step", 1)),
        transform=lambda code: _mask_transform(8, 8, code),
        address=123 + (idx - 1),
        data_key=f"counter_{idx}_cfg_raw",
        icon="mdi:counter",
    )


def _counter_connection_desc(idx: int) -> SelectDesc:
    return SelectDesc(
        key=f"counter_{idx}_connection_type_select",
        name=f"Counter {idx} Connection Type",
        options_map=CONNECTION_OPTIONS,
        get_code=lambda d, idx=idx: int(d.get(f"counter_{idx}_connection_type", 0)),
        transform=lambda code: _mask_transform(1, 1, code),
        address=123 + (idx - 1),
        data_key=f"counter_{idx}_cfg_raw",
        icon="mdi:connection",
    )


def _wireless_group_desc(idx: int) -> SelectDesc:
    return SelectDesc(
        key=f"wireless_{idx}_group",
        name=f"Wireless Sensor {idx} Group",
        options_map=GROUP_OPTIONS,
        get_code=lambda d, idx=idx: int(d.get(f"wireless_{idx}_group", 0)),
        transform=lambda code: _mask_transform(0, 8, code),
        address=7 + (idx - 1),
        data_key=f"wireless_{idx}_cfg_raw",
        icon="mdi:wifi",
    )


def _modbus_baud_desc() -> SelectDesc:
    return SelectDesc(
        key="modbus_baud",
        name="Modbus Baud Rate",
        options_map=BAUD_OPTIONS,
        get_code=lambda d: int(d.get("modbus_baud_code", 3)),
        transform=lambda code: _mask_transform(0, 8, code),
        address=5,
        data_key="modbus_cfg_raw",
        icon="mdi:speedometer",
        entity_category=EntityCategory.DIAGNOSTIC,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neptun Smart selects from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    descs: list[SelectDesc] = [
        _line_type_desc(1),
        _line_group_desc(1),
        _line_type_desc(2),
        _line_group_desc(2),
        _line_type_desc(3),
        _line_group_desc(3),
        _line_type_desc(4),
        _line_group_desc(4),
        _relay_desc("relay_alarm_group", "Relay on Alarm Group", 0),
        _relay_desc("relay_close_group", "Relay on Valve Close Group", 2),
        _modbus_baud_desc(),
    ]

    for idx in coordinator.installed_counters:
        descs.append(_counter_step_desc(idx))
        descs.append(_counter_connection_desc(idx))

    for idx in coordinator.installed_wireless_sensors:
        descs.append(_wireless_group_desc(idx))

    async_add_entities([NeptunRegisterSelect(coordinator, entry, d) for d in descs])


class NeptunRegisterSelect(NeptunSmartEntity, SelectEntity):
    """Register-backed select."""

    def __init__(self, coordinator, entry: ConfigEntry, desc: SelectDesc) -> None:
        super().__init__(coordinator, entry, desc.key, desc.name)
        self._desc = desc
        self._inverse = _inverse(desc.options_map)
        self._attr_options = list(desc.options_map.values())
        self._attr_icon = desc.icon
        self._attr_entity_category = desc.entity_category
        if desc.entity_category == EntityCategory.DIAGNOSTIC:
            self._attr_entity_registry_enabled_default = False

    @property
    def current_option(self) -> str | None:
        """Return selected option."""
        code = self._desc.get_code(self.coordinator.data)
        return self._desc.options_map.get(code)

    async def async_select_option(self, option: str) -> None:
        """Handle option change."""
        if option not in self._inverse:
            return
        code = self._inverse[option]
        await self.coordinator.async_write_register_transform(
            address=self._desc.address,
            data_key=self._desc.data_key,
            transform=self._desc.transform(code),
        )
