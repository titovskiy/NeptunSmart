"""The Neptun Smart integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_IGNORE_ZERO_COUNTER_VALUES,
    CONF_LEAK_LINES,
    CONF_SLAVE,
    CONF_WIRELESS_SENSORS,
    COORDINATOR,
    DEFAULT_LEAK_LINES,
    DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DEFAULT_TIMEOUT,
    DEFAULT_WIRELESS_SENSORS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import NeptunSmartCoordinator

NEPTUN_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=247)
        ),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=60)
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=3600)
        ),
        vol.Optional(CONF_WIRELESS_SENSORS, default=DEFAULT_WIRELESS_SENSORS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=5)
        ),
        vol.Optional(CONF_LEAK_LINES, default=DEFAULT_LEAK_LINES): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=4)
        ),
        vol.Optional(
            CONF_IGNORE_ZERO_COUNTER_VALUES,
            default=DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
        ): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [NEPTUN_ENTRY_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Neptun Smart from YAML and import entries."""
    if DOMAIN not in config:
        return True

    existing = {
        (
            entry.data[CONF_HOST],
            entry.data.get(CONF_PORT, DEFAULT_PORT),
            entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        )
        for entry in hass.config_entries.async_entries(DOMAIN)
    }

    for cfg in config[DOMAIN]:
        normalized_cfg = {
            **cfg,
            CONF_SLAVE: DEFAULT_SLAVE,
            CONF_WIRELESS_SENSORS: cfg.get(
                CONF_WIRELESS_SENSORS, DEFAULT_WIRELESS_SENSORS
            ),
            CONF_LEAK_LINES: cfg.get(CONF_LEAK_LINES, DEFAULT_LEAK_LINES),
            CONF_IGNORE_ZERO_COUNTER_VALUES: cfg.get(
                CONF_IGNORE_ZERO_COUNTER_VALUES,
                DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
            ),
        }
        key = (
            normalized_cfg[CONF_HOST],
            normalized_cfg.get(CONF_PORT, DEFAULT_PORT),
            normalized_cfg.get(CONF_SLAVE, DEFAULT_SLAVE),
        )
        if key in existing:
            continue
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=normalized_cfg,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Neptun Smart from a config entry."""
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
    timeout = entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    coordinator = NeptunSmartCoordinator(
        hass=hass,
        name=entry.title,
        host=host,
        port=port,
        slave=entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        timeout=timeout,
        update_interval=timedelta(seconds=scan_interval),
        ignore_zero_counter_values=entry.options.get(
            CONF_IGNORE_ZERO_COUNTER_VALUES,
            entry.data.get(
                CONF_IGNORE_ZERO_COUNTER_VALUES,
                DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
            ),
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {COORDINATOR: coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data: dict[str, Any] = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator: NeptunSmartCoordinator = data[COORDINATOR]
        await coordinator.async_close()

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options update."""
    await hass.config_entries.async_reload(entry.entry_id)
