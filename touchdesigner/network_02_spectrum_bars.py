"""
Network 02: Spectrum Bars
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

WHAT GETS BUILT:
  Audio Device In → Spectrum CHOP → CHOP to TOP → Transform TOP
  → Level TOP → Glow TOP → Null TOP (OUTPUT)

  The Spectrum CHOP runs an FFT on the audio buffer, outputting one channel
  per frequency bin. CHOP to TOP maps each channel to a pixel, creating a
  horizontal strip of frequency data. Transform rotates it 90° into vertical bars.

SIGNAL EXPLANATION:
  FFT window: 512 bins at 44100 Hz → each bin ≈ 86 Hz wide
  Channel 0  ≈ 0–86 Hz   (sub-bass)
  Channel 5  ≈ 430 Hz    (bass)
  Channel 30 ≈ 2580 Hz   (mids)
  Channel 100 ≈ 8600 Hz  (highs)

TROUBLESHOOTING:
  • Bars don't appear: increase Level brightness (try 10, 20, 50 — spectrum
    values are very small fractions of 1.0).
  • All bars same height: check Spectrum CHOP is cooking (click it, look for
    active waveform in viewer).
  • Wrong colors: select the Ramp TOP and adjust color stops manually in the UI.
"""


def build():
    p = me.parent()

    # ── Audio → Spectrum CHOP ─────────────────────────────────────────────────

    audio = p.create(audiodevInCHOP, 'audio_in')
    audio.nodeX, audio.nodeY = -900, 100

    # Spectrum CHOP: runs an FFT, outputting 'windowsize' frequency-bin channels.
    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 100
    spectrum.par.windowsize = 512   # number of frequency bins
    spectrum.setInput(0, audio)

    # Null CHOP: pass-through reference that other networks can tap into later.
    spec_data = p.create(nullCHOP, 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 100
    spec_data.setInput(0, spectrum)

    # ── CHOP to TOP: turn channel values into pixels ──────────────────────────

    # Each CHOP channel becomes one horizontal pixel column.
    # 512 channels → 512 pixels wide, 1 pixel tall.
    chop_top = p.create(choptoTOP, 'chop_to_top')
    chop_top.nodeX, chop_top.nodeY = -300, 100
    chop_top.setInput(0, spec_data)

    # ── Shape into vertical bars ──────────────────────────────────────────────

    # Rotate 90° so the 512-pixel row becomes a column, then scale vertically.
    # Result: left edge = bass, right edge = treble, height = energy.
    transform = p.create(transformTOP, 'bars_transform')
    transform.nodeX, transform.nodeY = -100, 100
    transform.par.rz  = 90       # rotate to make vertical bars
    transform.par.sy  = 12.0     # stretch to fill frame height
    transform.setInput(0, chop_top)

    # Spectrum values are very small — amplify them so bars are visible.
    level = p.create(levelTOP, 'level_amplify')
    level.nodeX, level.nodeY = 100, 100
    level.par.brightness = 30.0  # spectrum values are tiny; boost hard
    level.par.gamma      = 0.6   # gamma < 1 lifts quiet frequencies
    level.setInput(0, transform)

    # ── Color ─────────────────────────────────────────────────────────────────

    # Ramp TOP: generates a horizontal gradient used as a color lookup.
    # Default gives a grayscale gradient — customize color stops in the UI
    # (select ramp_color, go to Parameters, add stop points for bass=blue, treble=red).
    ramp = p.create(rampTOP, 'ramp_color')
    ramp.nodeX, ramp.nodeY = 100, -100
    ramp.par.type = 'horizontal'

    # Multiply: spectrum brightness × gradient color
    color_mult = p.create(compositeTOP, 'color_multiply')
    color_mult.nodeX, color_mult.nodeY = 300, 100
    color_mult.par.operand = 'multiply'
    color_mult.setInput(0, level)
    color_mult.setInput(1, ramp)

    # ── Glow and output ───────────────────────────────────────────────────────

    # Analyze overall energy to drive glow intensity
    energy = p.create(analyzeCHOP, 'analyze_energy')
    energy.nodeX, energy.nodeY = -700, -100
    energy.par.function = 'rms'
    energy.setInput(0, audio)

    energy_gain = p.create(mathCHOP, 'energy_gain')
    energy_gain.nodeX, energy_gain.nodeY = -500, -100
    energy_gain.par.gain = 5.0
    energy_gain.setInput(0, energy)

    energy_data = p.create(nullCHOP, 'energy_data')
    energy_data.nodeX, energy_data.nodeY = -300, -100
    energy_data.setInput(0, energy_gain)

    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 500, 100
    glow.par.size.expr     = "3 + op('energy_data')[0] * 20"
    glow.par.strength.expr = "0.2 + op('energy_data')[0] * 1.5"
    glow.setInput(0, color_mult)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 700, 100
    output.setInput(0, glow)

    print("=" * 50)
    print("Network 02: Spectrum Bars — BUILT")
    print("Container:", p.path)
    print()
    print("Next steps:")
    print("  1. Right-click OUTPUT → View")
    print("  2. If bars are invisible: select 'level_amplify'")
    print("     and push Brightness up to 50–200")
    print("  3. Customize colors: select 'ramp_color'")
    print("     and add color stops (blue=bass, white=treble)")
    print("=" * 50)


build()
