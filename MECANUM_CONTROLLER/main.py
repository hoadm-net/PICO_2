"""
PICO 2 - Joystick Controller with NRF24L01 TX

Wiring:
  Joystick:
    VRX  -> GP26 (ADC0)
    VRY  -> GP27 (ADC1)
    SW   -> GP22
    GND  -> GND
    VCC  -> 3.3V

  NRF24L01:
    VCC  -> 3.3V
    GND  -> GND
    CE   -> GP6
    CSN  -> GP5
    SCK  -> GP2
    MOSI -> GP3
    MISO -> GP4
    IRQ  -> GP7 (chưa dùng)
"""

from machine import SPI, Pin
import utime
from nrf24l01 import NRF24L01
from joy import get_direction, get_button

# ===== NRF24L01 SETUP ======
spi = SPI(
    0,
    baudrate=10_000_000,
    polarity=0,
    phase=0,
    sck=Pin(2),
    mosi=Pin(3),
    miso=Pin(4),
)
csn = Pin(5, mode=Pin.OUT, value=1)
ce  = Pin(6, mode=Pin.OUT, value=0)

nrf = NRF24L01(spi, csn, ce, channel=46, payload_size=2)

# TX address - must match RX address on the receiver side
TX_ADDRESS = b'\xe7\xe7\xe7\xe7\xe7'
nrf.open_tx_pipe(TX_ADDRESS)
nrf.stop_listening()

# ===== DIRECTION LABELS (for debug output) =====
DIR_LABELS = {
    0: "CENTER",
    1: "UP",
    2: "DOWN",
    3: "LEFT",
    4: "RIGHT",
    5: "UP_LEFT",
    6: "UP_RIGHT",
    7: "DOWN_LEFT",
    8: "DOWN_RIGHT",
}

print("Controller ready. Transmitting on channel 46...")

SEND_INTERVAL_MS = 5   # ~200 Hz — gửi liên tục để xe phản hồi tức thì
last_send_ms = 0
prev_direction = -1
prev_button = -1

while True:
    direction = get_direction()
    button    = get_button()
    now = utime.ticks_ms()

    if utime.ticks_diff(now, last_send_ms) >= SEND_INTERVAL_MS:
        try:
            nrf.send(bytes([direction, button]))
        except OSError:
            pass
        if direction != prev_direction or button != prev_button:
            print("TX -> dir:", DIR_LABELS.get(direction, direction), "| btn:", button)
            prev_direction = direction
            prev_button    = button
        last_send_ms = now
