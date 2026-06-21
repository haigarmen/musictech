# TouchDesigner: Audio-Reactive Motion Graphics

Five progressive network builder scripts for TouchDesigner.
Each script is a Python file you run **inside TouchDesigner** to
automatically construct a working audio-reactive network.

---

## How to run any script

1. Open TouchDesigner and create a new project.
2. Create a **Base COMP** at `/project1` (or change `BUILD_PATH` at the top of the script).
3. Inside the Base COMP, drop a **Text DAT**.
4. Paste the script contents into the Text DAT.
5. Set the Text DAT **Language** to **Python**.
6. Right-click the Text DAT → **Run Script**.
7. Right-click the `OUTPUT` node that appears → **View**.

---

## The five networks

### Network 01 — Basic Volume Pulse
**File:** `network_01_basic_volume_pulse.py`

The minimum viable audio-reactive graphic.
A circle pulses in size and brightness in direct proportion
to the overall loudness (RMS energy) of the incoming audio.

**New concepts:** Audio Device In, Analyze CHOP (RMS),
Filter CHOP (smoothing), Math CHOP (range remap),
parameter expressions linking CHOP values to TOP geometry.

```
Audio In → Analyze (RMS) → Filter → Math → Null CHOP
                                              ↓
                     Circle TOP (radius = audio) → Level → OUTPUT
```

---

### Network 02 — Spectrum Bars
**File:** `network_02_spectrum_bars.py`

The full frequency spectrum visualized as vertical bars.
Left = bass, right = treble. Color intensity tracks energy per bin.
Glow blooms on loud moments.

**New concepts:** Spectrum CHOP (FFT), CHOP to TOP
(channels → pixel texture), Transform TOP (rotate/scale),
Ramp TOP as a color LUT, Glow TOP.

```
Audio In → Spectrum CHOP → Filter → CHOP to TOP → Transform
                                                       ↓
                              Ramp (color) → Multiply → Glow → OUTPUT
```

---

### Network 03 — Noise Field with Feedback
**File:** `network_03_noise_field.py`

Three frequency bands (bass / mid / high) each control a different
visual dimension of an animated noise texture, with a feedback trail
that makes motion linger between frames.

| Band  | Controls                          |
|-------|-----------------------------------|
| Bass  | Noise period (zoom level)         |
| Mid   | Amplitude, hue rotation           |
| High  | Roughness, animation speed        |

**New concepts:** Multi-band Select CHOP, Noise TOP parameters,
HSV Adjust TOP, Feedback TOP (frame trail), Composite (add blend).

---

### Network 04 — 3D Particle System
**File:** `network_04_particle_system.py`

A full 3D pipeline: a grid of source points feeds a Particle SOP
whose birth rate, speed, and turbulence are all driven by audio.
Particles are lit with a Phong material, rendered, then glow-processed
and given a feedback trail.

| Band  | Controls                          |
|-------|-----------------------------------|
| Bass  | Particle birth rate               |
| Mid   | Upward velocity + emissive color  |
| High  | Turbulence / scattering           |

**New concepts:** Geo COMP, Camera COMP, Light COMP, Particle SOP,
Phong MAT (emissive expressions), Render TOP, full post-process stack.

---

### Network 05 — Real-Time Video Altered by Audio
**File:** `network_05_video_audio_reactive.py`

A live webcam feed is processed by a three-effect audio chain.
The camera image becomes the visual instrument: bass creates ghosting,
melodies shift colors, and transients ripple the image.

| Band  | Effect on video                   |
|-------|-----------------------------------|
| Bass  | Feedback depth (ghosting / smear) |
| Mid   | Hue rotation + oversaturation     |
| High  | Pixel displacement (ripple/jitter)|

**New concepts:** Video Device In TOP, Displace TOP (displacement map),
combining live video with procedural effects, all techniques unified.

```
Webcam → Displace (high) → HSV Shift (mid) ─→ Composite ─→ Glow → OUTPUT
                                               ↑
                              Feedback × (bass fade) ─────────────┘
```

---

## Tuning tips for all networks

- **Too little response?** Increase the `Gain` on the `math_bass`, `math_mid`,
  or `math_high` CHOPs. Start around 10–20 for a typical microphone.
- **Too much flickering?** Increase the `Width` on the `filter_*` CHOPs
  (try 0.08–0.15 for smoother, more musical motion).
- **Feedback too long / too short?** Adjust `brightness` expression in
  `feedback_fade`: values closer to 1.0 = longer trails.
- **No camera in Network 05?** Replace `videodevInTOP` with a
  **Movie File In TOP** and point it at any video file.

---

## Signal chain reference

```
Live audio
    │
    ▼
[Audio Device In CHOP]  ←─ microphone / line in
    │
    ▼
[Spectrum CHOP]         ←─ FFT: time domain → frequency domain
    │
    ├── [Select CHOP: bass  0–10]   → Analyze → Filter → Math → Null
    ├── [Select CHOP: mid  10–60]   → Analyze → Filter → Math → Null
    └── [Select CHOP: high 60–200]  → Analyze → Filter → Math → Null
                                           │          │         │
                                         bass        mid      high
                                           │          │         │
                                           ▼          ▼         ▼
                                       birth     hue shift  displacement
                                       trails    saturation  turbulence
```
