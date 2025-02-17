import colorsys
import dataclasses
import math
import time
from typing import TypeAlias

from mido import Message
import requests

from Controls import Controls

LEDS_LOWER = 55
LEDS_UPPER = 55
NUM_LEDS = LEDS_LOWER + LEDS_UPPER

CONTROL_NAMES = {
    "foreground_brightness": 73,
    "background_brightness": 72,
    "decay_speed": 74,
    "pressed_flicker_strength": 91,
    "pressed_flicker_speed": 93,
    "foreground_hue": 10,
    "background_hue": 42,
}

EventTime: TypeAlias = float
Number: TypeAlias = float | int


@dataclasses.dataclass
class KeyWobble:
    last_update: EventTime
    passed_pseudo_time: float


class PianoHandler:
    def __init__(self) -> None:
        self.colors = [0, 0, 0] * NUM_LEDS
        self.pressed_keys: dict[int, KeyWobble] = {}
        self.decaying_keys: dict[int, tuple[EventTime, KeyWobble]] = {}
        self.controls = Controls(CONTROL_NAMES)

    def handle_message(self, message: Message) -> None:
        match message:
            case Message(type="note_on", velocity=0) | Message(type="note_off"):
                self.decaying_keys[message.note] = EventTime(time.time()), self.pressed_keys[message.note]
                self.pressed_keys.pop(message.note)
            case Message(type="note_on"):
                self.pressed_keys[message.note] = KeyWobble(EventTime(time.time()), 0)
            case Message(type="control_change"):
                self.controls.handle_message(message)
            case unused_message:
                print(f"{unused_message=}")

    def update(self) -> None:
        self.calc_colors()
        self.send_colors()

    def calc_colors(self) -> None:
        # Background
        r, g, b = colorsys.hsv_to_rgb(
            self.controls.background_hue / 127,
            1,
            self.controls.background_brightness / 127,
        )
        r, g, b = unit_to_byte_range(r, g, b)
        self.colors = [r, g, b] * NUM_LEDS

        # Decaying keys
        now = time.time()
        if self.controls.decay_speed != 0:
            remaining_decay_keys = {}
            decay_levels = {}
            for key, decaying_key in self.decaying_keys.items():
                decay_level = min(1, (now - decaying_key[0]) / (self.controls.decay_speed * 0.01))
                if decay_level < 1:
                    remaining_decay_keys[key] = decaying_key
                    decay_levels[key] = decay_level

            self.decaying_keys = remaining_decay_keys
            for key, decay_level in decay_levels.items():
                flickered_brightness = self.calculate_flickered_brightness(self.decaying_keys[key][1], now)
                hue = self.controls.foreground_hue * (1 - decay_level) + self.controls.background_hue * decay_level
                brightness = (
                    flickered_brightness * (1 - decay_level) + self.controls.background_brightness / 127 * decay_level
                )
                r, g, b = colorsys.hsv_to_rgb(hue / 127, 1, brightness)
                r, g, b = unit_to_byte_range(r, g, b)

                led_indices = map_note_to_leds(key)
                for led_index in led_indices:
                    self.colors[led_index * 3 : (led_index + 1) * 3] = [r, g, b]

        # Active keys
        for key, key_wobble in self.pressed_keys.items():
            flickered_brightness = self.calculate_flickered_brightness(key_wobble, now)
            r, g, b = colorsys.hsv_to_rgb(
                self.controls.foreground_hue / 127,
                1,
                flickered_brightness,
            )
            r, g, b = unit_to_byte_range(r, g, b)
            led_indices = map_note_to_leds(key)
            for led_index in led_indices:
                self.colors[led_index * 3 : (led_index + 1) * 3] = [r, g, b]

    def calculate_flickered_brightness(self, key_wobble: KeyWobble, now: float) -> float:
        real_time_since_last_update = now - key_wobble.last_update
        key_wobble.last_update = now
        key_wobble.passed_pseudo_time += real_time_since_last_update * 0.2 * self.controls.pressed_flicker_speed
        pre_flicker_value = self.controls.foreground_brightness / 127
        phase = math.sin(key_wobble.passed_pseudo_time)
        flicker_modifier = 1 - (self.controls.pressed_flicker_strength / 127) * (phase + 1) / 2
        return flicker_modifier * pre_flicker_value

    def send_colors(self) -> None:
        payload = bytes(self.colors)
        requests.post(
            "http://192.168.178.26/ColorFromPayload",
            headers={"Content-Type": "application/octet-stream"},
            data=payload,
        )


def map_note_to_leds(note: int) -> list[int]:
    black_keys = []
    for i in range(22, 107, 12):
        black_keys.extend([i, i + 3, i + 5, i + 8, i + 10])

    if note in black_keys:
        key_range = range(22, 106)
        led_range = range(NUM_LEDS - 1, LEDS_LOWER, -1)
    else:
        key_range = range(21, 109)
        led_range = range(0, LEDS_LOWER - 1)

    key_center = math.floor(map_range(note, key_range.start, key_range.stop, led_range.start, led_range.stop))

    return [led for led in [key_center - 1, key_center, key_center + 1] if led in led_range]


def map_range(
    value: Number, start_range_low: Number, start_range_high: Number, end_rage_low: Number, end_range_high: Number
) -> float:
    end_range_span = end_range_high - end_rage_low
    proportion = (value - start_range_low) / (start_range_high - start_range_low)
    new_value = end_rage_low + end_range_span * proportion
    return new_value


def unit_to_byte_range(*values: float) -> list[int]:
    mapped_values = []
    for value in values:
        mapped_values.append(math.floor(value * 255))
    return mapped_values
