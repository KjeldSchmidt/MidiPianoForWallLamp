
import fluidsynth
import time

print("Starting FluidSynth...")

fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="alsa")

print("Loading SoundFont...")

sfid = fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")

if sfid == -1:
    raise RuntimeError("Could not load SoundFont")

fs.program_select(0, sfid, 0, 0)

print("Playing middle C...")

fs.noteon(0, 60, 100)
time.sleep(2)
fs.noteoff(0, 60)

time.sleep(0.5)

print("Playing a chord...")

for note in [60, 64, 67]:
    fs.noteon(0, note, 100)

time.sleep(2)

for note in [60, 64, 67]:
    fs.noteoff(0, note)

time.sleep(0.5)

print("Shutting down...")
fs.delete()

print("Done!")

