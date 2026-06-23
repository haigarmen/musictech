# TouchDesigner: Audio-Reactive Motion Graphics

Five Python network builder scripts. Each one, when run **inside TouchDesigner**,
automatically wires together a complete audio-reactive network.

---

## How to run any script

These scripts run **inside TouchDesigner**, not from the command line.

1. Open TouchDesigner and start a new project
2. **Right-click** in the network editor → **Add Operator** → **COMP** → **Base**
3. **Double-click** the Base COMP to go inside it
4. **Right-click** inside it → **Add Operator** → **DAT** → **Text**
5. Click the Text DAT to select it, then paste the full script into its text area
6. In the Text DAT's **Parameters** panel, set **Language** to **Python**
7. **Right-click** the Text DAT → **Run Script**
8. The network will be built inside the Base COMP
9. **Right-click** the `OUTPUT` node → **View** to see the result

> **If `audio_in` shows a red cook error ("No audio device"):**
> Click the `audio_in` operator → open its Parameters → go to the **Audio Device** page
> → select your microphone or line input from the **Device** dropdown.

> **If nothing reacts to audio:**
> Select the `math_gain` node → increase its **Gain** parameter. Raw RMS values
> are often very small (0.001–0.05). Try Gain = 10, 20, or 50.

---

## The five networks

### Network 01 — Basic Volume Pulse
**`network_01_basic_volume_pulse.py`**

The minimum viable audio-reactive graphic: a circle that grows and glows with
the overall loudness of the audio.

**Signal chain:**
```
Audio Device In → Analyze (RMS) → Math (gain) → Null CHOP (audio_data)
                                                         ↓
                             Circle TOP (radius expression) → Level → OUTPUT
```

**What's new:** Audio Device In CHOP, Analyze CHOP (RMS), Math CHOP (gain),
parameter expressions, Circle TOP, Level TOP.

---

### Network 02 — Spectrum Bars
**`network_02_spectrum_bars.py`**

The full frequency spectrum displayed as vertical bars. Bass on the left,
treble on the right. Bar height = energy in that frequency band.

**Signal chain:**
```
Audio Device In → Spectrum CHOP → Null CHOP
                       ↓
               CHOP to TOP → Transform (rotate 90°) → Level → Ramp (color LUT)
               → Composite (multiply) → Glow → OUTPUT
```

**What's new:** Spectrum CHOP (FFT), CHOP to TOP, Transform TOP,
Ramp TOP as color LUT, Glow TOP.

---

### Network 03 — Noise Field with Feedback
**`network_03_noise_field.py`**

Three frequency bands control different properties of an animated noise texture,
with a feedback trail that makes bright areas linger between frames.

| Band | Spectrum bins | Effect |
|------|--------------|--------|
| Bass | 1–4 (~86–344 Hz) | Noise zoom / period |
| Mid | 15–35 (~1290–3010 Hz) | Amplitude, hue rotation |
| High | 60–120 (~5160–10320 Hz) | Roughness, animation speed |

**What's new:** Direct spectrum bin indexing in expressions, Noise TOP,
HSV Adjust TOP, Feedback TOP (frame trail).

---

### Network 04 — 3D Particle System
**`network_04_particle_system.py`**

A full 3D rendering pipeline. Particles are born from a grid, simulated
each frame, and rendered through a camera with a Phong material.

| Band | Effect |
|------|--------|
| Bass | Particle birth rate (kick = burst of particles) |
| Mid | Upward velocity + emissive color |
| High | Turbulence / scattering |

> **Manual step required after building:**
> Select `particle_geo` → Parameters → Render tab → set **Material** to `phong_mat`

**What's new:** Geo COMP, Camera COMP, Light COMP, Particle SOP,
Phong MAT, Render TOP.

---

### Network 05 — Real-Time Video Altered by Audio
**`network_05_video_audio_reactive.py`**

A live webcam feed processed by three audio-driven effects stacked in series.
The camera image becomes the visual instrument.

| Band | Effect on video |
|------|----------------|
| Bass | Feedback depth — ghost trails on kick/bass hits |
| Mid | Hue rotation + saturation — color shifts on melody |
| High | Pixel displacement — image ripples on transients |

> **Manual step required:** Select `video_in` → set **Device** to your webcam.
> No webcam? Replace `video_in` with a Movie File In TOP pointing at a video file.

**What's new:** Video Device In TOP, Displace TOP, combining live video
with procedural effects, all previous techniques unified.

---

## How the spectrum bin expressions work

Networks 03–05 skip the Select CHOP and reference frequency data directly:

```python
# 44100 Hz sample rate / 512-point FFT → each bin ≈ 86 Hz wide
# op('spectrum_data')[n] = energy at bin n (0-indexed)

BASS  = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+...) * 60, 0, 1)"
MID   = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+...) * 90, 0, 1)"
HIGH  = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+...) * 120, 0, 1)"
```

The `× 60 / × 90 / × 120` multipliers amplify the tiny FFT values into
a 0–1 range. **Increase these if the effect is too subtle; decrease if it clips.**

---

## Tuning reference

| Problem | Fix |
|---------|-----|
| Nothing reacts | Increase `math_gain` Gain (try 10, 20, 50) |
| Response too jittery | The Spectrum CHOP has an Overlap parameter — increase it |
| Feedback trails never fade | Lower the `feedback_fade` brightness expression upper bound |
| Feedback trails fade too fast | Raise the upper bound (max 1.0 = trails never clear) |
| Spectrum bars invisible | Increase `level_amplify` Brightness (spectrum values are tiny) |
| Particles don't appear | Inside `particle_geo`, select `particles` → increase Birth Rate |
| Video camera not found | Select `video_in` → set Device index (0, 1, 2...) |
