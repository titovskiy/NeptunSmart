"""Data coordinator for Neptun Smart."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BIT_DUAL_ZONE_MODE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    MASK_ZONE_BOTH,
    REG_ALARM_MODE,
    REG_COUNTER_SETTINGS_COUNT,
    REG_COUNTER_SETTINGS_START,
    REG_LINE_CFG_1_2,
    REG_LINE_CFG_3_4,
    REG_LEAK_SENSOR_RAW,
    REG_MODBUS_CFG,
    REG_RELAY_CFG,
    REG_WATER_COUNTERS_REG_COUNT,
    REG_WATER_COUNTERS_START,
    REG_WIRELESS_PARAMS_START,
    REG_WIRELESS_SENSOR_COUNT,
    REG_WIRELESS_SENSORS_START,
)

_LOGGER = logging.getLogger(__name__)


class NeptunSmartCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data fetches from Neptun Smart controller."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: int,
        slave: int,
        timeout: int = DEFAULT_TIMEOUT,
        update_interval: timedelta | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{name} ({host}:{port}, slave {slave})",
            update_interval=update_interval or timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.slave = slave
        self.timeout = timeout
        self.unique_prefix = f"{host}_{port}_{slave}".replace(".", "_")

        self._client = AsyncModbusTcpClient(host=host, port=port, timeout=timeout)
        self._lock = None

    @property
    def installed_counters(self) -> list[int]:
        """Return detected counter indexes based on counter settings."""
        if not self.data:
            return list(range(1, 9))
        return [
            idx
            for idx in range(1, 9)
            if bool(self.data.get(f"counter_{idx}_enabled"))
        ]

    @property
    def installed_wireless_sensors(self) -> list[int]:
        """Return detected wireless sensor indexes."""
        if not self.data:
            return []
        count = max(0, min(50, int(self.data.get("wireless_sensor_count", 0))))
        return list(range(1, count + 1))

    @property
    def detected_leak_lines(self) -> list[int]:
        """Return detected leak line indexes."""
        if not self.data:
            return [1]
        count = max(1, min(4, int(self.data.get("detected_leak_lines", 1))))
        return list(range(1, count + 1))

    async def async_test_connection(self) -> bool:
        """Check whether connection and basic read works."""
        if not self._client.connected:
            ok = await self._client.connect()
            if not ok:
                return False

        try:
            response = await self._read_holding(REG_ALARM_MODE, 1)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Neptun Smart test connection failed for %s:%s (slave=%s)",
                self.host,
                self.port,
                self.slave,
            )
            return False

        return response is not None

    async def async_close(self) -> None:
        """Close Modbus client connection."""
        self._client.close()

    async def _ensure_connected(self) -> None:
        """Ensure TCP session to controller is active."""
        if self._client.connected:
            return
        if not await self._client.connect():
            raise UpdateFailed(f"Unable to connect to {self.host}:{self.port}")

    async def _call_with_slave(
        self,
        method: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Call pymodbus function with compatible arg/kwarg combinations."""
        last_error: Exception | None = None
        for slave_kw in ("device_id", "slave", "unit"):
            for use_positional in (False, True):
                call_kwargs = dict(kwargs)
                call_kwargs[slave_kw] = self.slave
                try:
                    if use_positional:
                        return await method(*args, **call_kwargs)
                    return await method(**call_kwargs)
                except TypeError as err:
                    last_error = err

        if last_error is not None:
            raise last_error
        raise UpdateFailed("No compatible slave argument for pymodbus call")

    async def _read_holding(self, address: int, count: int) -> list[int]:
        """Read holding registers and return raw register list."""
        await self._ensure_connected()
        response = await self._call_with_slave(
            self._client.read_holding_registers,
            address,
            count,
            address=address,
            count=count,
        )
        if response.isError():
            raise UpdateFailed(
                f"Modbus read error at address {address} (count={count}): {response}"
            )
        return list(response.registers)

    async def _write_register(self, address: int, value: int) -> None:
        """Write one holding register."""
        await self._ensure_connected()
        response = await self._call_with_slave(
            self._client.write_register,
            address,
            value,
            address=address,
            value=value,
        )
        if response.isError():
            raise UpdateFailed(
                f"Modbus write error at address {address} (value={value}): {response}"
            )

    async def _write_registers(self, address: int, values: list[int]) -> None:
        """Write multiple holding registers."""
        await self._ensure_connected()
        response = await self._call_with_slave(
            self._client.write_registers,
            address,
            values,
            address=address,
            values=values,
        )
        if response.isError():
            raise UpdateFailed(
                f"Modbus write error at address {address} (values={values}): {response}"
            )

    async def async_write_alarm_mode(self, transform: Callable[[int], int]) -> None:
        """Apply transformation to alarm/mode register value and persist it."""
        await self.async_write_register_transform(
            address=REG_ALARM_MODE,
            data_key="alarm_mode_raw",
            transform=transform,
        )

    async def async_write_register_transform(
        self,
        address: int,
        data_key: str | None,
        transform: Callable[[int], int],
    ) -> None:
        """Apply transformation to a register and write it back."""
        from asyncio import Lock

        if self._lock is None:
            self._lock = Lock()

        async with self._lock:
            current = self.data.get(data_key) if (self.data and data_key) else None
            if current is None:
                current = (await self._read_holding(address, 1))[0]

            new_value = max(0, min(0xFFFF, int(transform(int(current)))))
            if new_value == current:
                return

            await self._write_register(address, new_value)

        await self.async_request_refresh()

    async def async_write_counter_step(self, counter_index: int, step_value: int) -> None:
        """Write counting step for counter module (registers 123..130, bits 8..15)."""
        from asyncio import Lock

        if self._lock is None:
            self._lock = Lock()

        if not 1 <= counter_index <= 8:
            raise UpdateFailed(f"Invalid counter index: {counter_index}")

        step_value = int(step_value)
        if step_value not in (1, 10, 100):
            raise UpdateFailed(
                f"Invalid counter step {step_value}; allowed values are 1, 10, 100"
            )
        address = REG_COUNTER_SETTINGS_START + (counter_index - 1)
        data_key = f"counter_{counter_index}_cfg_raw"

        async with self._lock:
            current = self.data.get(data_key) if self.data else None
            if current is None:
                current = (await self._read_holding(address, 1))[0]

            new_value = (int(current) & 0x00FF) | ((step_value & 0xFF) << 8)
            if new_value == current:
                return

            await self._write_register(address, new_value)

        await self.async_request_refresh()

    async def async_write_counter_calibration(
        self, counter_index: int, value_m3: float
    ) -> None:
        """Set current counter value for calibration."""
        from asyncio import Lock

        if self._lock is None:
            self._lock = Lock()

        if not 1 <= counter_index <= 8:
            raise UpdateFailed(f"Invalid counter index: {counter_index}")

        scaled = max(0, int(round(float(value_m3) * 1000)))
        scaled = min(scaled, 0x7FFFFFFF)
        hi = (scaled >> 16) & 0xFFFF
        lo = scaled & 0xFFFF
        address = REG_WATER_COUNTERS_START + (counter_index - 1) * 2

        async with self._lock:
            await self._write_registers(address, [hi, lo])

        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all required registers from controller."""
        from asyncio import Lock

        if self._lock is None:
            self._lock = Lock()

        async with self._lock:
            try:
                reg0_to_6 = await self._read_holding(REG_ALARM_MODE, 7)
                wireless: list[int] = []
                wireless_params: list[int] = []
                if reg0_to_6[REG_WIRELESS_SENSOR_COUNT] > 0:
                    wireless_count = max(0, min(50, reg0_to_6[REG_WIRELESS_SENSOR_COUNT]))
                    wireless_params = await self._read_holding(
                        REG_WIRELESS_PARAMS_START, wireless_count
                    )
                    wireless = await self._read_holding(
                        REG_WIRELESS_SENSORS_START, wireless_count
                    )
                water_regs = await self._read_holding(
                    REG_WATER_COUNTERS_START, REG_WATER_COUNTERS_REG_COUNT
                )
                counter_settings = await self._read_holding(
                    REG_COUNTER_SETTINGS_START, REG_COUNTER_SETTINGS_COUNT
                )
            except Exception as err:  # pylint: disable=broad-except
                raise UpdateFailed(str(err)) from err

        alarm_mode = reg0_to_6[0]
        line_cfg_1_2 = reg0_to_6[REG_LINE_CFG_1_2]
        line_cfg_3_4 = reg0_to_6[REG_LINE_CFG_3_4]
        leak_sensor_raw = reg0_to_6[REG_LEAK_SENSOR_RAW]
        relay_cfg = reg0_to_6[REG_RELAY_CFG]
        modbus_cfg = reg0_to_6[REG_MODBUS_CFG]
        wireless_count = reg0_to_6[REG_WIRELESS_SENSOR_COUNT]
        line_types = [
            (line_cfg_1_2 >> 10) & 0x3,
            (line_cfg_1_2 >> 2) & 0x3,
            (line_cfg_3_4 >> 10) & 0x3,
            (line_cfg_3_4 >> 2) & 0x3,
        ]
        line_groups = [
            (line_cfg_1_2 >> 8) & 0x3,
            line_cfg_1_2 & 0x3,
            (line_cfg_3_4 >> 8) & 0x3,
            line_cfg_3_4 & 0x3,
        ]
        detected_leak = 1
        for idx in range(1, 5):
            leak_active = bool(leak_sensor_raw & (1 << (idx - 1)))
            cfg_active = line_types[idx - 1] != 0 or line_groups[idx - 1] != 0
            if leak_active or cfg_active:
                detected_leak = idx

        data: dict[str, Any] = {
            "alarm_mode_raw": alarm_mode,
            "line_cfg_1_2_raw": line_cfg_1_2,
            "line_cfg_3_4_raw": line_cfg_3_4,
            "leak_sensor_raw": leak_sensor_raw,
            "wireless_sensor_count": wireless_count,
            "detected_leak_lines": detected_leak,
            "dual_zone_mode": bool(alarm_mode & BIT_DUAL_ZONE_MODE),
            "relay_cfg_raw": relay_cfg,
            "modbus_cfg_raw": modbus_cfg,
            "modbus_address": (modbus_cfg >> 8) & 0xFF,
            "modbus_baud_code": modbus_cfg & 0xFF,
            "relay_alarm_group": relay_cfg & 0x3,
            "relay_close_group": (relay_cfg >> 2) & 0x3,
        }

        _decode_line_config(data, line_cfg_1_2, 1, 2)
        _decode_line_config(data, line_cfg_3_4, 3, 4)

        if wireless_count > 0:
            for idx, value in enumerate(wireless_params, start=1):
                data[f"wireless_{idx}_cfg_raw"] = value
                data[f"wireless_{idx}_group"] = value & 0xFF
            for idx, value in enumerate(wireless, start=1):
                data[f"wireless_{idx}_raw"] = value
                data[f"wireless_{idx}_alarm"] = bool(value & (1 << 0))
                data[f"wireless_{idx}_category"] = bool(value & (1 << 1))
                data[f"wireless_{idx}_loss"] = bool(value & (1 << 2))
                data[f"wireless_{idx}_signal"] = ((value >> 3) & 0x7) * 25
                data[f"wireless_{idx}_battery"] = (value >> 8) & 0xFF

        for i in range(0, len(water_regs), 2):
            hi = water_regs[i]
            lo = water_regs[i + 1]
            value = (hi << 16) | lo
            if value & 0x80000000:
                value -= 0x100000000
            counter_idx = (i // 2) + 1
            slot = ((counter_idx - 1) // 2) + 1
            port = 1 if counter_idx % 2 else 2
            data[f"water_counter_s{slot}_p{port}"] = round(value * 0.001, 3)

        for idx, value in enumerate(counter_settings, start=1):
            data[f"counter_{idx}_cfg_raw"] = value
            data[f"counter_{idx}_step"] = (value >> 8) & 0xFF
            data[f"counter_{idx}_namur_error"] = (value >> 2) & 0x3
            data[f"counter_{idx}_connection_type"] = (value >> 1) & 0x1
            data[f"counter_{idx}_enabled"] = bool(value & 0x1)
            data[f"counter_{idx}_status_code"] = value & 0xF

        data["detected_counters"] = sum(
            1 for idx in range(1, 9) if data.get(f"counter_{idx}_enabled")
        )

        return data


def _decode_line_config(
    data: dict[str, Any],
    value: int,
    line_a: int,
    line_b: int,
) -> None:
    """Decode line type and group from packed register."""
    data[f"line_{line_a}_type"] = (value >> 10) & 0x3
    data[f"line_{line_a}_group"] = (value >> 8) & 0x3
    data[f"line_{line_b}_type"] = (value >> 2) & 0x3
    data[f"line_{line_b}_group"] = value & 0x3


def set_bits(value: int, mask: int) -> int:
    """Set bitmask in integer value."""
    return value | mask


def clear_bits(value: int, mask: int) -> int:
    """Clear bitmask in integer value."""
    return value & ~mask


def toggle_zone_1_on(value: int) -> int:
    """Handle Zona 1 ON behavior according to dual zone mode."""
    if not (value & BIT_DUAL_ZONE_MODE):
        return set_bits(value, MASK_ZONE_BOTH)
    return set_bits(value, 1 << 8)


def toggle_zone_1_off(value: int) -> int:
    """Handle Zona 1 OFF behavior according to dual zone mode."""
    if not (value & BIT_DUAL_ZONE_MODE):
        return clear_bits(value, MASK_ZONE_BOTH)
    return clear_bits(value, 1 << 8)
