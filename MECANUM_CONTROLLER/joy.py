from machine import ADC, Pin
import utime

# ===== DIRECTION CONSTANT =====
CENTER = 0
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4
UP_LEFT = 5
UP_RIGHT = 6
DOWN_LEFT = 7
DOWN_RIGHT = 8


# ===== JOYSTICK =====
xAxis = ADC(26)
yAxis = ADC(27)
swBtn = Pin(22, Pin.IN, Pin.PULL_UP)  # SW: active LOW

X_CENTER = 33736
Y_CENTER = 33736

DEADZONE = 5000


def get_direction():

    x = xAxis.read_u16()
    y = yAxis.read_u16()

    dx = x - X_CENTER
    dy = y - Y_CENTER

    if abs(dx) < DEADZONE and abs(dy) < DEADZONE:
        return CENTER

    if dx < -DEADZONE and dy < -DEADZONE:
        return UP_LEFT

    if dx > DEADZONE and dy < -DEADZONE:
        return UP_RIGHT

    if dx < -DEADZONE and dy > DEADZONE:
        return DOWN_LEFT

    if dx > DEADZONE and dy > DEADZONE:
        return DOWN_RIGHT

    if dy < -DEADZONE:
        return UP

    if dy > DEADZONE:
        return DOWN

    if dx < -DEADZONE:
        return LEFT

    if dx > DEADZONE:
        return RIGHT


def get_button():
    """Return 1 if button is pressed, 0 otherwise."""
    return 0 if swBtn.value() else 1
