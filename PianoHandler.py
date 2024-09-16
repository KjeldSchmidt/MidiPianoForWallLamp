import colorsys
import math

import mido
import requests


NUM_LEDS = 110
LEDS_LOWER = 54
LEDS_UPPER = 56


class PianoHandler:
    def __init__(self):
        self.colors = [0, 0, 0] * NUM_LEDS
        self.pressed_keys = set()
        self.decaying_keys = set()
        self.base_hue = 0.115
        self.background_brightness = 0.25
        self.foreground_brightness = 1
        pass

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
            print("control change")
            if message.control == 73:
                self.foreground_brightness = message.value/255
                print(f"self.foreground_brightness = {message.value / 255}")
            if message.control == 72:
                self.background_brightness = message.value/255
                print(f"self.background_brightness = {message.value / 255}")

        self.send_colors()

    def calc_colors(self):
        hue = self.base_hue
        r, g, b = colorsys.hsv_to_rgb(hue, 1, self.background_brightness)
        r, g, b = unit_to_byte_range(r, g, b)
        self.colors = [r, g, b] * NUM_LEDS

        pressed_hue = self.base_hue + 0.25
        r, g, b = colorsys.hsv_to_rgb(pressed_hue, 1, self.foreground_brightness)
        r, g, b = unit_to_byte_range(r, g, b)
        for key in self.pressed_keys:
            led_indices = map_note_to_leds(key)
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
        key_center = map_range(note, 22, 106, 110, 56)
    else:
        key_center = map_range(note, 21, 108, 0, 55)

    return [key_center-1, key_center, key_center+1]


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