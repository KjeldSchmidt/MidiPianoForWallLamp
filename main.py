import random

import mido
import requests


def run_with_keyboard():
    with mido.open_input() as inport:
        print("Ready!")
        for message in inport:
            print(f"{message=}")
            if message.type == "note_on" and message.velocity != 0:
                print(f"{message.note=}, {message.velocity=}")
                r = random.Random()
                red_channel = r.randint(50, 255)
                green_channel = r.randint(50, 255)
                blue_channel = r.randint(50, 255)
                response = requests.get(
                    "http://192.168.178.26/setMode",
                    params={
                        "newMode": "SingleColor",
                        "color": f"0x{red_channel:x}{green_channel:x}{blue_channel:x}",
                    },
                )


def run_synthetic():
    response = requests.get(
        "http://192.168.178.26/setMode",
        params={
            "newMode": "Piano",
            "Payload": f"hello",
        },
    )

run_with_keyboard()