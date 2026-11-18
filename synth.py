from mido import Message
import requests


import fluidsynth


class Synth:
    def __init__(
        self,
        soundfont="/usr/share/sounds/sf2/FluidR3_GM.sf2",
        gain=0.5,
        driver="alsa"
    ):
        self.fs = fluidsynth.Synth(gain=gain)

        # Start audio output
        self.fs.start(driver=driver)

        # Load SoundFont
        self.sfid = self.fs.sfload(soundfont)

        if self.sfid == -1:
            self.fs.delete()
            raise RuntimeError(f"Could not load SoundFont: {soundfont}")

        # Select Acoustic Grand Piano (MIDI program 0)
        self.fs.program_select(0, self.sfid, 0, 0)

    def handle_message(self, msg):
        """Forward a Mido MIDI message to FluidSynth."""

        channel = getattr(msg, "channel", 0)

        if msg.type == "note_on":
            if msg.velocity == 0:
                self.fs.noteoff(channel, msg.note)
            else:
                self.fs.noteon(channel, msg.note, msg.velocity)

        elif msg.type == "note_off":
            self.fs.noteoff(channel, msg.note)

        elif msg.type == "control_change":
            self.fs.cc(channel, msg.control, msg.value)

        elif msg.type == "program_change":
            self.fs.program_change(channel, msg.program)

        elif msg.type == "pitchwheel":
            # Mido uses -8192 to 8191; FluidSynth uses 0 to 16383
            self.fs.pitch_bend(channel, msg.pitch + 8192)

        elif msg.type == "aftertouch":
            self.fs.channel_pressure(channel, msg.value)

        elif msg.type == "polytouch":
            self.fs.key_pressure(channel, msg.note, msg.value)

    def close(self):
        """Stop FluidSynth and release audio resources."""
        if self.fs is not None:
            self.fs.delete()
            self.fs = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


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
