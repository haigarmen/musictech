"""
Network 02: Spectrum Bars
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

WHAT GETS BUILT:
  Audio Device In → Spectrum CHOP → Null CHOP
  → CHOP to TOP → Transform (rotate 90°) → Level → Ramp (color LUT)
  → Composite (multiply) → Glow → Null TOP (OUTPUT)

  The Spectrum CHOP runs an FFT on the audio, outputting one channel per
  frequency bin. CHOP to TOP maps each channel to one pixel. Transform
  rotates the 1-pixel-tall row 90° into vertical bars.

  Left edge ≈ 0 Hz (sub-bass), right edge ≈ 22 kHz (air).
  Bar height = energy in that frequency range.
"""


def td_op(*names):
    for name in names:
        try:
            result = eval(name)
            if result is not None:
                return result
        except NameError:
            continue
    chops = sorted(k for k in dir() if k.endswith('CHOP'))
    tops  = sorted(k for k in dir() if k.endswith('TOP'))
    print(f"ERROR: operator type(s) not found: {names}")
    print(f"Run in Textport: [x for x in dir() if x.endswith('CHOP')]")
    print(f"Sample CHOPs: {chops[:6]}  Sample TOPs: {tops[:6]}")
    raise NameError(f"TD types not found: {names}")


def build():
    p = me.parent()

    # ── Audio → Spectrum CHOP ─────────────────────────────────────────────────

    audio = p.create(td_op('audiodevInCHOP'), 'audio_in')
    audio.nodeX, audio.nodeY = -900, 100

    # Spectrum CHOP: FFT → 512 output channels (one per frequency bin)
    spectrum = p.create(td_op('spectrumCHOP'), 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 100
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = p.create(td_op('nullCHOP'), 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 100
    spec_data.setInput(0, spectrum)

    # ── CHOP to TOP ───────────────────────────────────────────────────────────

    # Each of the 512 CHOP channels becomes one pixel column.
    # Result: 512 × 1 pixel texture where brightness = frequency energy.
    chop_top = p.create(td_op('choptoTOP'), 'chop_to_top')
    chop_top.nodeX, chop_top.nodeY = -300, 100
    chop_top.setInput(0, spec_data)

    # Rotate 90° → columns become bars. Scale vertically to fill the frame.
    transform = p.create(td_op('transformTOP'), 'bars_transform')
    transform.nodeX, transform.nodeY = -100, 100
    transform.par.rz = 90
    transform.par.sy = 12.0
    transform.setInput(0, chop_top)

    # Spectrum values are very small fractions — amplify to make bars visible.
    # If bars are still invisible, increase Brightness further (try 50–200).
    level = p.create(td_op('levelTOP'), 'level_amplify')
    level.nodeX, level.nodeY = 100, 100
    level.par.brightness = 30.0
    level.par.gamma      = 0.6     # lift quieter frequencies
    level.setInput(0, transform)

    # ── Color ─────────────────────────────────────────────────────────────────

    # Ramp TOP: horizontal gradient used as a color LUT.
    # Default is grayscale — after building, select ramp_color and add
    # colour stops in the parameters (e.g. blue at 0, cyan at 0.5, white at 1).
    ramp = p.create(td_op('rampTOP'), 'ramp_color')
    ramp.nodeX, ramp.nodeY = 100, -100
    ramp.par.type = 'horizontal'

    # Multiply spectrum brightness by the colour gradient.
    color_mult = p.create(td_op('compositeTOP'), 'color_multiply')
    color_mult.nodeX, color_mult.nodeY = 300, 100
    color_mult.par.operand = 'multiply'
    color_mult.setInput(0, level)
    color_mult.setInput(1, ramp)

    # ── Energy-driven glow ────────────────────────────────────────────────────

    energy = p.create(td_op('analyzeCHOP'), 'analyze_energy')
    energy.nodeX, energy.nodeY = -700, -100
    energy.par.function = 'rms'
    energy.setInput(0, audio)

    e_gain = p.create(td_op('mathCHOP'), 'energy_gain')
    e_gain.nodeX, e_gain.nodeY = -500, -100
    e_gain.par.gain = 5.0
    e_gain.setInput(0, energy)

    e_data = p.create(td_op('nullCHOP'), 'energy_data')
    e_data.nodeX, e_data.nodeY = -300, -100
    e_data.setInput(0, e_gain)

    glow = p.create(td_op('glowTOP'), 'glow')
    glow.nodeX, glow.nodeY = 500, 100
    glow.par.size.expr     = "3 + op('energy_data')[0] * 20"
    glow.par.strength.expr = "0.2 + op('energy_data')[0] * 1.5"
    glow.setInput(0, color_mult)

    output = p.create(td_op('nullTOP'), 'OUTPUT')
    output.nodeX, output.nodeY = 700, 100
    output.setInput(0, glow)

    print("=" * 55)
    print("Network 02: Spectrum Bars — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ If bars are invisible: select level_amplify,")
    print("  push Brightness to 50–200")
    print("→ Customise colours: select ramp_color, add stops")
    print("  (blue=bass, cyan=mid, white=treble)")
    print("=" * 55)


build()
