import base64
import math
import colorsys

import mido
import requests

NUM_LEDS = 110

def run_with_keyboard():
    with mido.open_input() as inport:
        print("Ready!")
        for message in inport:
            print(f"{message=}")
            if message.type == "note_on" and message.velocity != 0:
                print(f"{message.note=}, {message.velocity=}")
                hue = (message.note-21)/(108 - 21)
                print(f"{hue=}")
                r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
                r, g, b = unit_to_byte_range(r, g, b)
                colors = [r, g, b] * NUM_LEDS
                payload = bytes(colors)
                response = requests.post(
                    "http://192.168.178.26/ColorFromPayload",
                    headers={'Content-Type': 'application/octet-stream'},
                    data=payload,
                )
                print(response.status_code)
                print(response.text)


def run_synthetic():
    payload = b"\x00\xFF\x00" * 110

    colors = []
    num_leds = 110
    for i in range(num_leds):
        hue = i/num_leds
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        colors.append(math.floor(r * 255))
        colors.append(math.floor(g * 255))
        colors.append(math.floor(b * 255))

    payload = bytes(colors)

    response = requests.post(
        "http://192.168.178.26/ColorFromPayload",
        headers={'Content-Type': 'application/octet-stream'},
        data=payload,
    )
    print(response.status_code)
    print(response.text)


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

run_with_keyboard()
