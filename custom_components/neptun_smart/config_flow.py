"""Config flow for Neptun Smart integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENABLE_WIRELESS,
    CONF_LEAK_LINES,
    CONF_SLAVE,
    CONF_WIRELESS_SENSORS,
    DEFAULT_ENABLE_WIRELESS,
    DEFAULT_LEAK_LINES,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DEFAULT_TIMEOUT,
    DEFAULT_WIRELESS_SENSORS,
    DOMAIN,
)
from .coordinator import NeptunSmartCoordinator


class NeptunSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neptun Smart."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input = _normalize_input(user_input)

            if _is_configured(self, normalized_input):
                return self.async_abort(reason="already_configured")

            ok = await _validate_connection(self.hass, normalized_input)
            if ok:
                return self.async_create_entry(
                    title=normalized_input[CONF_NAME],
                    data=normalized_input,
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Import config from YAML."""
        normalized_input = _normalize_input(user_input)

        if _is_configured(self, normalized_input):
            return self.async_abort(reason="already_configured")

        ok = await _validate_connection(self.hass, normalized_input)
        if not ok:
            return self.async_abort(reason="cannot_connect")

        return self.async_create_entry(
            title=normalized_input[CONF_NAME],
            data=normalized_input,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> NeptunSmartOptionsFlow:
        """Get options flow handler."""
        return NeptunSmartOptionsFlow(config_entry)


class NeptunSmartOptionsFlow(config_entries.OptionsFlow):
    """Handle Neptun Smart options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            normalized = _normalize_input(user_input)
            options = {
                CONF_SCAN_INTERVAL: normalized[CONF_SCAN_INTERVAL],
                CONF_ENABLE_WIRELESS: normalized[CONF_ENABLE_WIRELESS],
                CONF_WIRELESS_SENSORS: normalized[CONF_WIRELESS_SENSORS],
                CONF_LEAK_LINES: normalized[CONF_LEAK_LINES],
            }
            return self.async_create_entry(title="", data=options)

        current_scan_interval = _safe_int(
            self._config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
            DEFAULT_SCAN_INTERVAL,
            minimum=5,
            maximum=3600,
        )
        current_enable_wireless = _safe_bool(
            self._config_entry.options.get(
                CONF_ENABLE_WIRELESS,
                self._config_entry.data.get(CONF_ENABLE_WIRELESS, DEFAULT_ENABLE_WIRELESS),
            ),
            DEFAULT_ENABLE_WIRELESS,
        )
        current_wireless_sensors = _safe_int(
            self._config_entry.options.get(
                CONF_WIRELESS_SENSORS,
                self._config_entry.data.get(CONF_WIRELESS_SENSORS, DEFAULT_WIRELESS_SENSORS),
            ),
            DEFAULT_WIRELESS_SENSORS,
            minimum=1,
            maximum=5,
        )
        current_leak_lines = _safe_int(
            self._config_entry.options.get(
                CONF_LEAK_LINES,
                self._config_entry.data.get(CONF_LEAK_LINES, DEFAULT_LEAK_LINES),
            ),
            DEFAULT_LEAK_LINES,
            minimum=1,
            maximum=4,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                    vol.Required(
                        CONF_ENABLE_WIRELESS,
                        default=current_enable_wireless,
                    ): bool,
                    vol.Required(
                        CONF_WIRELESS_SENSORS,
                        default=current_wireless_sensors,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
                    vol.Required(
                        CONF_LEAK_LINES,
                        default=current_leak_lines,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
                }
            ),
        )


def _schema(user_input: dict[str, Any] | None) -> vol.Schema:
    """Build dynamic form schema."""
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(
                CONF_TIMEOUT,
                default=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
            vol.Required(
                CONF_ENABLE_WIRELESS,
                default=user_input.get(CONF_ENABLE_WIRELESS, DEFAULT_ENABLE_WIRELESS),
            ): bool,
            vol.Required(
                CONF_WIRELESS_SENSORS,
                default=user_input.get(CONF_WIRELESS_SENSORS, DEFAULT_WIRELESS_SENSORS),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
            vol.Required(
                CONF_LEAK_LINES,
                default=user_input.get(CONF_LEAK_LINES, DEFAULT_LEAK_LINES),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
        }
    )


def _normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user/import input with defaults."""
    return {
        **data,
        CONF_SLAVE: DEFAULT_SLAVE,
        CONF_ENABLE_WIRELESS: _safe_bool(
            data.get(CONF_ENABLE_WIRELESS, DEFAULT_ENABLE_WIRELESS),
            DEFAULT_ENABLE_WIRELESS,
        ),
        CONF_WIRELESS_SENSORS: _safe_int(
            data.get(CONF_WIRELESS_SENSORS, DEFAULT_WIRELESS_SENSORS),
            DEFAULT_WIRELESS_SENSORS,
            minimum=1,
            maximum=5,
        ),
        CONF_LEAK_LINES: _safe_int(
            data.get(CONF_LEAK_LINES, DEFAULT_LEAK_LINES),
            DEFAULT_LEAK_LINES,
            minimum=1,
            maximum=4,
        ),
    }


def _safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    """Convert value to int and clamp to expected range."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, result))


def _safe_bool(value: Any, default: bool) -> bool:
    """Convert value to bool, including legacy string values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default
    if value is None:
        return default
    return bool(value)


def _is_configured(flow: NeptunSmartConfigFlow, data: dict[str, Any]) -> bool:
    """Check if same host/port/slave is already configured."""
    for entry in flow._async_current_entries():
        if (
            entry.data.get(CONF_HOST) == data.get(CONF_HOST)
            and entry.data.get(CONF_PORT) == data.get(CONF_PORT)
            and entry.data.get(CONF_SLAVE, DEFAULT_SLAVE)
            == data.get(CONF_SLAVE, DEFAULT_SLAVE)
        ):
            return True
    return False


async def _validate_connection(hass, data: dict[str, Any]) -> bool:
    """Try connecting and reading one register to verify settings."""
    coordinator = NeptunSmartCoordinator(
        hass=hass,
        name=data[CONF_NAME],
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        slave=data[CONF_SLAVE],
        timeout=data[CONF_TIMEOUT],
    )
    try:
        return await coordinator.async_test_connection()
    finally:
        await coordinator.async_close()
