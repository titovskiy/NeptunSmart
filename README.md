# Neptun Smart Home Assistant Integration (Modbus TCP)

Кастомная интеграция для подключения контроллера Neptun Smart по Modbus TCP.

## Возможности

- Чтение основных регистров состояния (alarm/mode, leak raw, wireless raw, счетчики воды).
- Автоматическое декодирование:
  - батареи и уровня сигнала беспроводных датчиков;
  - бинарных флагов тревог и режимов;
  - водосчетчиков `S1..S4 / P1..P2`.
- Управление режимами и кранами через `switch` сущности.
- Настройка через UI (`Добавить интеграцию`) или импорт из `configuration.yaml`.

## Установка

Скопируйте папку `custom_components/neptun_smart_local` в ваш Home Assistant:

`<config>/custom_components/neptun_smart_local`

Перезапустите Home Assistant.

## Настройка через UI

1. `Settings` -> `Devices & Services` -> `Add Integration`.
2. Выберите `Neptun Smart`.
3. Заполните `host`, `port`, `timeout`, `scan_interval` и при необходимости включите `ignore_zero_counter_values` для фильтрации шумовых нулей счетчиков.

## Настройка через YAML (импорт)

```yaml
neptun_smart_local:
  - name: Neptun Smart
    host: 192.168.1.198
    port: 503
    timeout: 3
    scan_interval: 10
    ignore_zero_counter_values: true
    enable_wireless: false
    wireless_sensors: 1
    leak_lines: 1
```

После запуска запись будет импортирована как config entry.

## Сущности

Интеграция создает:

- `sensor`:
  - `Alarm and Mode Raw`, `Leak Sensor Raw`
  - `Connected Wireless Sensors`, `Wireless Sensor 1..5 Raw`, `Battery Level Sensor 1..5`, `Sensor Signal Level 1..5` (только при `enable_wireless: true`)
  - `Water counter S1..S4 P1..P2`
- `binary_sensor`:
  - ключевые биты контроллера (`Dual Zone Mode`, `Floor Washing Mode`, зоны, и т.д.)
  - `LeakSensor 1..N` (по параметру `leak_lines`, 1..4)
  - статус каждого беспроводного датчика (`alarm/category/loss`) по параметру `wireless_sensors` (1..5), только при `enable_wireless: true`
- `switch`:
  - `Zona 1`, `Zona 2`, `Zona 1+2`
  - `Dual Zone Mode`, `Floor Washing Mode`, `Keypad Locks`
  - `Closing taps on sensor lost`
  - `Procedure for connecting wireless devices` (только при `enable_wireless: true`)
