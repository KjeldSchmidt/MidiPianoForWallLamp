from typing import Mapping

import mido


class Controls:
    def __init__(self, control_names: Mapping[str, int]):
        self.values: Mapping[int, int] = {index: 0 for index in range(0, 100)}
        self.control_names_to_channel = control_names
        self.channel_to_control_names = {value: key for key, value in control_names.items()}

    def handle_message(self, message: mido.Message):
        self.values[message.control] = message.value
        name_to_print = self.channel_to_control_names.get(message.control, message.control)
        print(f"control change: {name_to_print} = {message.value}")

    def __getattr__(self, name: str) -> int:
        if name not in self.control_names_to_channel:
            raise KeyError(f"Trying to access named control '{name}' not found in {self.control_names_to_channel=}")

        return self.values[self.control_names_to_channel[name]]

