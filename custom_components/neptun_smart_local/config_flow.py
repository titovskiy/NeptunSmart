"""Config flow for Neptun Smart integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_IGNORE_ZERO_COUNTER_VALUES,
    CONF_SLAVE,
    DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DEFAULT_TIMEOUT,
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
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized = _normalize_input(user_input)
            ok = await _validate_connection(self.hass, normalized)
            if not ok:
                errors["base"] = "cannot_connect"
            else:
                options = {
                    CONF_HOST: normalized[CONF_HOST],
                    CONF_PORT: normalized[CONF_PORT],
                    CONF_TIMEOUT: normalized[CONF_TIMEOUT],
                    CONF_SCAN_INTERVAL: normalized[CONF_SCAN_INTERVAL],
                    CONF_IGNORE_ZERO_COUNTER_VALUES: normalized[
                        CONF_IGNORE_ZERO_COUNTER_VALUES
                    ],
                }
                return self.async_create_entry(title="", data=options)

        current_host = str(
            self._config_entry.options.get(
                CONF_HOST,
                self._config_entry.data.get(CONF_HOST, ""),
            )
        )
        current_port = _safe_int(
            self._config_entry.options.get(
                CONF_PORT,
                self._config_entry.data.get(CONF_PORT, DEFAULT_PORT),
            ),
            DEFAULT_PORT,
            minimum=1,
            maximum=65535,
        )
        current_timeout = _safe_int(
            self._config_entry.options.get(
                CONF_TIMEOUT,
                self._config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ),
            DEFAULT_TIMEOUT,
            minimum=1,
            maximum=60,
        )
        current_scan_interval = _safe_int(
            self._config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
            DEFAULT_SCAN_INTERVAL,
            minimum=5,
            maximum=3600,
        )
        current_ignore_zero_counter_values = bool(
            self._config_entry.options.get(
                CONF_IGNORE_ZERO_COUNTER_VALUES,
                self._config_entry.data.get(
                    CONF_IGNORE_ZERO_COUNTER_VALUES,
                    DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
                ),
            )
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=current_host): str,
                    vol.Required(CONF_PORT, default=current_port): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                    vol.Required(CONF_TIMEOUT, default=current_timeout): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=60)
                    ),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                    vol.Required(
                        CONF_IGNORE_ZERO_COUNTER_VALUES,
                        default=current_ignore_zero_counter_values,
                    ): bool,
                }
            ),
            errors=errors,
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
                CONF_IGNORE_ZERO_COUNTER_VALUES,
                default=user_input.get(
                    CONF_IGNORE_ZERO_COUNTER_VALUES,
                    DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
                ),
            ): bool,
        }
    )


def _normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user/import input with defaults."""
    return {
        **data,
        CONF_SLAVE: DEFAULT_SLAVE,
        CONF_IGNORE_ZERO_COUNTER_VALUES: bool(
            data.get(
                CONF_IGNORE_ZERO_COUNTER_VALUES,
                DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
            )
        ),
    }


def _safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    """Convert value to int and clamp to expected range."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, result))


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
        name=data.get(CONF_NAME, DEFAULT_NAME),
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        slave=data[CONF_SLAVE],
        timeout=data[CONF_TIMEOUT],
        ignore_zero_counter_values=data.get(
            CONF_IGNORE_ZERO_COUNTER_VALUES,
            DEFAULT_IGNORE_ZERO_COUNTER_VALUES,
        ),
    )
    try:
        return await coordinator.async_test_connection()
    finally:
        await coordinator.async_close()
