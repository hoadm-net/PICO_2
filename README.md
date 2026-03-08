# PICO_2 — IoT Projects với Raspberry Pi Pico 2

Tập hợp các project nhỏ để học và thực hành IoT trên board **Raspberry Pi Pico 2** với **MicroPython**.

## Board

**Raspberry Pi Pico 2** — vi điều khiển RP2350, dual-core Cortex-M33, 520KB SRAM, 4MB Flash.

## Ngôn ngữ

**MicroPython** — Python chạy trực tiếp trên vi điều khiển, phù hợp để prototyping nhanh các ứng dụng IoT.

- Firmware: https://micropython.org/download/RPI_PICO2/
- Tool nạp code: [MicroPico](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go) (VS Code extension)

## Projects

| Folder | Mô tả |
|---|---|
| [`LCD/`](LCD/) | Hiển thị text lên LCD 20×4 qua I2C (PCF8574) |
| [`MECANUM_CONTROLLER/`](MECANUM_CONTROLLER/) | Tay cầm joystick truyền lệnh không dây qua NRF24L01 |
