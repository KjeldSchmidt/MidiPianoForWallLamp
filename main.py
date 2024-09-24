import math
import colorsys

import mido
import requests

from PianoHandler import PianoHandler


def run_with_keyboard():
    piano_handler = PianoHandler()
    with mido.open_input() as inport:
        print("Ready!")
        while True:
            for message in inport.iter_pending():
                piano_handler.handle_message(message)

            piano_handler.update()


def run_synthetic():
    colors = []
    num_leds = 110
    for i in range(num_leds):
        hue = i / num_leds
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        colors.append(math.floor(r * 255))
        colors.append(math.floor(g * 255))
        colors.append(math.floor(b * 255))

    payload = bytes(colors)

    response = requests.post(
        "http://192.168.178.26/ColorFromPayload",
        headers={"Content-Type": "application/octet-stream"},
        data=payload,
    )
    print(response.status_code)
    print(response.text)


run_with_keyboard()
