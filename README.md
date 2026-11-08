# Neptun Smart Home Assistant Integration (Modbus TCP)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#)
[![Language: RU](https://img.shields.io/badge/Язык-Русский-lightgrey.svg)](README_ru.md)

*Read this in other languages: [Русский](README_ru.md)*

Custom Home Assistant integration for connecting the **Neptun Smart** (Нептун Смарт) water leak protection controller via **Modbus TCP**.

---

## Features

- **Full Bilingual Localization**: English and Russian support for configuration flows, options, entities, and selector options.
- **Leak Detection & Monitoring**:
  - Read wired leak sensor lines (`Leak sensor 1..4`) with automatic detection.
  - Monitor wireless sensor states: alarm, connection loss, category, battery percentage, and signal strength.
- **Water Metering**:
  - Decode water meter pulse counters `S1..S4 / P1..P2` (up to 8 channels) converted to cubic meters ($m^3$).
  - Calibration of meter readings via `number` entities.
  - Optional zero-reading filter (`ignore_zero_counter_values`) for noisy pulses.
- **Valve & Mode Control**:
  - Control valves for Zone 1, Zone 2, and Zone 1 + Zone 2 simultaneously via `switch` entities.
  - Toggle modes: Dual Zone Mode, Floor Washing Mode, Keypad Locks, and Wireless Sensor Pairing mode.
  - Configure tap closing behavior when sensors lose signal.
- **Advanced Configuration via Modbus**:
  - Line input types (`Sensors` / `Button`) and valve groups.
  - Event relays (on alarm and on valve close).
  - Counter parameters: step size (`1`, `10`, `100` L), connection type (`Normal` / `Namur`), and status.
  - Module Modbus address and baud rate.
- **Resilience**:
  - Configurable `unavailable_grace_period` to prevent entity flapping on unstable Wi-Fi connections.
  - Read-before-write validation and safety locks for atomic Modbus operations.

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant.
2. Go to **Integrations** -> Click the three dots in the top right corner -> **Custom repositories**.
3. Add repository URL: `https://github.com/titovskiy/NeptunSmart` with category **Integration**.
4. Search for `Neptun Smart` and click **Download**.
5. Restart Home Assistant.

### Method 2: Manual Installation

1. Copy the `custom_components/neptun_smart_local` folder to your Home Assistant directory:
   ```text
   <config>/custom_components/neptun_smart_local
   ```
2. Restart Home Assistant.

---

## Configuration

### UI Setup (Config Flow)

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for and select **Neptun Smart**.
3. Fill in the connection settings:
   - **Name**: Controller display name (default: `Neptun Smart`).
   - **Host**: IP address of the Neptun Smart module.
   - **Port**: Modbus TCP port (default: `503`).
   - **Timeout (seconds)**: Network timeout in seconds (default: `3`).
   - **Scan interval (seconds)**: Polling interval (default: `10`).
   - **Delay before unavailable (seconds)**: Grace period before marking entities unavailable on connection loss (default: `30`).
   - **Ignore zero values for water counters**: Filter out temporary zero readings from counters (default: `false`).

### UI Options Flow

You can change any of the connection settings (`host`, `port`, `timeout`, `scan_interval`, `unavailable_grace_period`, `ignore_zero_counter_values`) at any time by clicking **Configure** on the integration card.

### YAML Setup (Import)

You can also define the configuration in `configuration.yaml`. Upon startup, Home Assistant will automatically import it into a UI config entry:

```yaml
neptun_smart_local:
  - name: Neptun Smart
    host: 192.168.1.198
    port: 503
    timeout: 3
    scan_interval: 10
    unavailable_grace_period: 30
    ignore_zero_counter_values: true
```

---

## Entities

The integration creates the following entities under a single device:

### Sensors (`sensor`)
- **Water meters**: `Water counter S{slot} P{port}` ($m^3$) with total increasing state class.
- **Wireless sensors**:
  - `Connected wireless sensors` (count)
  - `Wireless sensor {N} raw` (raw telemetry)
  - `Battery level sensor {N}` (%)
  - `Sensor signal level {N}` (%)
- **Diagnostics**:
  - `Alarm and mode raw`
  - `Leak sensor raw`
  - `Detected counters`
  - `Counter {N} status code`
  - `Counter {N} connection type`
  - `Counter {N} Namur error`

### Binary Sensors (`binary_sensor`)
- **Zones & Alarms**:
  - `Zone 1`, `Zone 2` (valve open status)
  - `Alarm zone 1`, `Alarm zone 2`
- **Lines & Sensors**:
  - `Leak sensor 1..4` (wired lines status)
  - `Presence of alarm sensor {N}` (wireless)
  - `Availability of category sensor {N}`
  - `Sensor loss sensor {N}`
  - `Battery drain in wireless sensors`
  - `Lost connection with wireless sensors`
- **Modes & Flags**:
  - `Dual zone mode`
  - `Floor washing mode`
  - `Keypad locks`
  - `Close group 1 on sensor loss`
  - `Close group 2 on sensor loss`
  - `Counter {N} status`

### Switches (`switch`)
- **Valve Control**:
  - `Zone 1` (Open / Close Zone 1)
  - `Zone 2` (Open / Close Zone 2, active when Dual Zone Mode is on)
  - `Zone 1 + Zone 2` (Simultaneous control)
- **Modes**:
  - `Dual zone mode`
  - `Floor washing mode`
  - `Keypad locks`
  - `Closing taps on sensor lost`
  - `Close group 1 on sensor loss`
  - `Close group 2 on sensor loss`
  - `Add new wireless sensor` (pairing mode)
  - `Counter {N} enabled`

### Numbers (`number`)
- `Counter {N} calibration` ($m^3$, allow setting the current meter reading)
- `Modbus address` (controller Modbus ID, diagnostic)

### Selects (`select`)
- `Line {N} input type`: `Sensors` or `Button`
- `Line {N} valve group`: `None`, `Group 1`, `Group 2`, or `Group 1 + 2`
- `Relay on alarm group`: `None`, `Group 1`, `Group 2`, or `Group 1 + 2`
- `Relay on valve close group`: `None`, `Group 1`, `Group 2`, or `Group 1 + 2`
- `Counter {N} step`: `1`, `10`, or `100` L
- `Counter {N} connection type`: `Normal` or `Namur`
- `Wireless sensor {N} group`: `None`, `Group 1`, `Group 2`, or `Group 1 + 2`
- `Modbus baud rate`: Baud rate selection (diagnostic)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
