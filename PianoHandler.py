import colorsys
import math

import mido
import requests

from Controls import Controls

LEDS_LOWER = 55
LEDS_UPPER = 55
NUM_LEDS = LEDS_LOWER + LEDS_UPPER

CONTROL_NAMES = {
    "foreground_brightness": 73,
    "background_brightness": 72,
    "foreground_hue": 10,
    "background_hue": 42,
}


class PianoHandler:
    def __init__(self):
        self.colors = [0, 0, 0] * NUM_LEDS
        self.pressed_keys = set()
        self.decaying_keys = set()
        self.base_hue = 0.115
        self.controls = Controls(CONTROL_NAMES)

    def handle_message(self, message: mido.Message):
        if message.type == "note_on" and message.velocity != 0:
            self.pressed_keys.add(message.note)
            print(f"Turning on {message.note=} at {message.velocity=}")
        if message.type == "note_on" and message.velocity == 0:
            print(f"Turning off {message.note=}")
            self.pressed_keys.remove(message.note)
            self.decaying_keys.add(message.note)
        if message.type == "program_change" and message.program < 9:
            self.base_hue = 0.115 * message.program
        if message.type == "control_change":
            self.controls.handle_message(message)

        self.send_colors()

    def calc_colors(self):
        r, g, b = colorsys.hsv_to_rgb(self.controls.background_hue / 127, 1, self.controls.background_brightness / 255)
        r, g, b = unit_to_byte_range(r, g, b)
        self.colors = [r, g, b] * NUM_LEDS

        r, g, b = colorsys.hsv_to_rgb(self.controls.foreground_hue / 127, 1, self.controls.foreground_brightness / 255)
        r, g, b = unit_to_byte_range(r, g, b)
        for key in self.pressed_keys:
            led_indices = map_note_to_leds(key)
            print(led_indices)
            for led_index in led_indices:
                self.colors[led_index*3:(led_index+1)*3] = [r, g, b]

    def send_colors(self):
        self.calc_colors()
        payload = bytes(self.colors)
        response = requests.post(
            "http://192.168.178.26/ColorFromPayload",
            headers={'Content-Type': 'application/octet-stream'},
            data=payload,
        )
        # print(response.status_code)
        # print(response.text)


def map_note_to_leds(note: int) -> list[int]:
    black_keys = []
    for i in range(22, 107, 12):
        black_keys.extend([i, i+3, i+5, i+8, i+10,])

    if note in black_keys:
        key_range = range(22, 106)
        led_range = range(NUM_LEDS-1, LEDS_LOWER, -1)
    else:
        key_range = range(21, 109)
        led_range = range(0, LEDS_LOWER-1)

    key_center = map_range(note, key_range.start, key_range.stop, led_range.start, led_range.stop)

    return [led for led in [key_center-1, key_center, key_center+1] if led in led_range]


def map_range(value, start_range_low, start_range_high, end_rage_low, end_range_high):
    end_range_span = end_range_high-end_rage_low
    proportion = (value-start_range_low)/(start_range_high - start_range_low)
    new_value = math.floor(end_rage_low + end_range_span*proportion)
    return new_value


def unit_to_byte_range(*values: float):
    mapped_values = []
    for value in values:
        mapped_values.append(math.floor(value*255))
    return mapped_values