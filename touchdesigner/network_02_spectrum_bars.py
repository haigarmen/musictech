"""
Network 02: Spectrum Bars
==========================
Turns the full frequency spectrum into a scrolling bar graph.
Each vertical column corresponds to a frequency bin: bass on the left,
treble on the right. Color shifts from deep blue (quiet) to hot white (loud).

Signal Flow:
    [Audio Device In] → [Spectrum CHOP] → [CHOP to TOP] → [Transform TOP]
                                                                  ↓
    [Ramp TOP (color LUT)] → [Multiply (composite)] → [Null TOP: OUTPUT]
                                    ↑
                          [Level TOP (brightness)]

Concepts introduced:
    - Spectrum CHOP: FFT — converts time-domain audio to frequency domain
    - CHOP to TOP: maps CHOP channel values onto pixels (1 channel = 1 pixel row)
    - Transform TOP: flip / scale the image into vertical bars
    - Ramp TOP: a color gradient used as a lookup table
    - Math TOP: pixel-wise multiply to apply the color LUT to the spectrum data

How to run:
    Same as Network 01 — paste into a Text DAT inside a Base COMP and Run Script.
"""

BUILD_PATH = '/project1'


def build():
    p = op(BUILD_PATH)
    if p is None:
        print(f"ERROR: '{BUILD_PATH}' not found.")
        return

    # ── Audio → Spectrum ─────────────────────────────────────────────────────

    audio_in = p.create(audiodevInCHOP, 'audio_in')
    audio_in.nodeX, audio_in.nodeY = -1000, 200
    audio_in.par.rate = 44100

    # Spectrum CHOP performs an FFT on the audio buffer.
    # windowsize controls frequency resolution; more bins = smoother bars.
    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -800, 200
    spectrum.par.windowsize = 512   # 512 frequency bins output
    spectrum.par.overlap    = 0.75  # 75% window overlap for temporal smoothness
    spectrum.setInput(0, audio_in)

    # Smooth the spectrum so bars don't flicker chaotically
    filt = p.create(filterCHOP, 'filter_spectrum')
    filt.nodeX, filt.nodeY = -600, 200
    filt.par.width = 0.03
    filt.setInput(0, spectrum)

    # CHOP to TOP: each CHOP channel becomes a horizontal row of pixels.
    # With 512 channels from Spectrum, we get a 512-pixel-wide texture.
    chop_to_top = p.create(choptoTOP, 'chop_to_top')
    chop_to_top.nodeX, chop_to_top.nodeY = -400, 200
    chop_to_top.par.chanoffset  = 0
    chop_to_top.par.numchans    = 512
    chop_to_top.setInput(0, filt)

    # ── Shape the spectrum texture into vertical bars ──────────────────────

    # Flip the 1-pixel-tall texture 90° so frequencies run left→right
    # and amplitude grows upward
    transform = p.create(transformTOP, 'transform_rotate')
    transform.nodeX, transform.nodeY = -200, 200
    transform.par.rz  = 90     # rotate 90° to make vertical bars
    transform.par.sy  = 8.0    # stretch vertically so bars have height
    transform.par.extend = 'black'
    transform.setInput(0, chop_to_top)

    # Boost and normalize the spectrum amplitude for visibility
    level_spec = p.create(levelTOP, 'level_spectrum')
    level_spec.nodeX, level_spec.nodeY = 0, 200
    level_spec.par.brightness = 3.0   # spectrum values are small; amplify them
    level_spec.par.gamma      = 0.5   # gamma < 1 lifts shadows (quieter frequencies)
    level_spec.setInput(0, transform)

    # ── Color lookup table ────────────────────────────────────────────────────

    # Ramp TOP generates a horizontal gradient: black → blue → cyan → white
    # We'll use this as a color LUT by multiplying against the spectrum.
    ramp = p.create(rampTOP, 'color_ramp')
    ramp.nodeX, ramp.nodeY = 0, 0
    ramp.par.type = 'horizontal'
    # Set ramp color points: pos 0 = black, 0.3 = deep blue, 0.7 = cyan, 1.0 = white
    # (In TD, ramp color points are edited in the UI; script sets the type here.)

    # Multiply: spectrum brightness × ramp color = colored bars
    multiply = p.create(compositeTOP, 'multiply_color')
    multiply.nodeX, multiply.nodeY = 200, 200
    multiply.par.operand = 'multiply'
    multiply.setInput(0, level_spec)
    multiply.setInput(1, ramp)

    # ── Overall brightness tied to average energy ─────────────────────────

    # Analyze average energy to modulate overall glow
    analyze = p.create(analyzeCHOP, 'analyze_avg')
    analyze.nodeX, analyze.nodeY = -800, 0
    analyze.par.function = 'rms'
    analyze.setInput(0, audio_in)

    audio_null = p.create(nullCHOP, 'audio_data')
    audio_null.nodeX, audio_null.nodeY = -600, 0
    audio_null.setInput(0, analyze)

    # Glow effect: halo around bright bars on loud moments
    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 400, 200
    glow.par.size.expr    = "2 + op('audio_data')['chan1'] * 20"
    glow.par.strength.expr = "0.3 + op('audio_data')['chan1'] * 1.5"
    glow.setInput(0, multiply)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 600, 200
    output.setInput(0, glow)

    print("✓  Network 02 built.")
    print("   You'll see ~512 frequency bars colored by energy level.")
    print("   TIP: Select the Ramp TOP and manually set color stops in the UI.")

build()
