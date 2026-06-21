"""
Network 03: Audio-Reactive Noise Field
=======================================
Three separate frequency bands (bass, mid, high) each control a different
visual parameter of an animated noise texture, with a feedback trail that
makes the motion linger. This introduces multi-band audio analysis and
screen-space feedback compositing.

Signal Flow:
    [Audio In] → [Spectrum] → [Select CHOP x3] → [Analyze x3] → [Filter x3]
                                                                        ↓
                                             bass → Noise period
                                             mid  → Noise amplitude / color hue
                                             high → Noise speed / roughness
                                                          ↓
    [Noise TOP] → [HSV Adjust] → [Composite over Feedback] → [Feedback TOP]
                                                 ↓
                                          [Null TOP: OUTPUT]

Concepts introduced:
    - Multi-band analysis: splitting the spectrum into frequency regions
    - Select CHOP: extract a sub-range of channels from Spectrum output
    - Noise TOP: procedural animated texture with many audio-driveable params
    - HSV Adjust TOP: shift hue/saturation/value independently
    - Feedback TOP: reads the previous frame → creates motion trails
    - Composite over feedback: new frame blended with fading history

How to run:
    Paste into a Text DAT inside a Base COMP and Run Script.
"""

BUILD_PATH = '/project1'


def build():
    p = op(BUILD_PATH)
    if p is None:
        print(f"ERROR: '{BUILD_PATH}' not found.")
        return

    # ── Audio input ───────────────────────────────────────────────────────────

    audio_in = p.create(audiodevInCHOP, 'audio_in')
    audio_in.nodeX, audio_in.nodeY = -1200, 400
    audio_in.par.rate = 44100

    # Full frequency spectrum via FFT
    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -1000, 400
    spectrum.par.windowsize = 512
    spectrum.par.overlap    = 0.75
    spectrum.setInput(0, audio_in)

    # ── Three band analyzers ──────────────────────────────────────────────────
    # Spectrum CHOP outputs 512 channels (bins 0..511).
    # At 44100 Hz with a 512-point FFT, each bin ≈ 86 Hz wide.
    # Bass:   bins  0-10  (~0–860 Hz)
    # Mid:    bins 10-60  (~860–5160 Hz)
    # High:   bins 60-200 (~5160–17200 Hz)

    band_defs = [
        ('bass',  0,   10, -800, 600),
        ('mid',   10,  60, -800, 400),
        ('high',  60, 200, -800, 200),
    ]

    nulls = {}
    for name, ch_start, ch_end, nx, ny in band_defs:

        # Select the frequency range from the spectrum
        sel = p.create(selectCHOP, f'select_{name}')
        sel.nodeX, sel.nodeY = nx, ny
        sel.par.chanstart = ch_start
        sel.par.chanend   = ch_end - 1
        sel.setInput(0, spectrum)

        # Average energy in this band
        analyze = p.create(analyzeCHOP, f'analyze_{name}')
        analyze.nodeX, analyze.nodeY = nx + 200, ny
        analyze.par.function = 'average'
        analyze.setInput(0, sel)

        # Smooth to remove click artifacts
        filt = p.create(filterCHOP, f'filter_{name}')
        filt.nodeX, filt.nodeY = nx + 400, ny
        filt.par.width = 0.05
        filt.setInput(0, analyze)

        # Scale each band up (spectrum values are small fractions)
        math = p.create(mathCHOP, f'math_{name}')
        math.nodeX, math.nodeY = nx + 600, ny
        math.par.gain = 12.0    # amplify — tune per your signal level
        math.par.clamp = True
        math.par.clampmin = 0.0
        math.par.clampmax = 1.0
        math.setInput(0, filt)

        null = p.create(nullCHOP, f'data_{name}')
        null.nodeX, null.nodeY = nx + 800, ny
        null.setInput(0, math)
        nulls[name] = null

    # ── Noise texture ─────────────────────────────────────────────────────────
    # Bass  → period (zooms in/out of noise — low end = large structures)
    # Mid   → amplitude (intensity of the noise pattern)
    # High  → roughness / speed (sharp, fast detail on transients)

    noise = p.create(noiseTOP, 'noise_field')
    noise.nodeX, noise.nodeY = -200, 400
    # Period: at rest the noise is mid-scale; bass expands it dramatically
    noise.par.periodx.expr = "0.3 + op('data_bass')['chan1'] * 1.5"
    noise.par.periody.expr = "0.3 + op('data_bass')['chan1'] * 1.5"
    # Amplitude: brightness of the noise (mid frequencies drive energy)
    noise.par.amp.expr     = "0.4 + op('data_mid')['chan1']  * 1.2"
    # Speed: how fast the noise animates (high freq = flutter / shimmer)
    noise.par.rough.expr   = "0.5 + op('data_high')['chan1'] * 0.45"
    # Slow base crawl; high band adds extra speed bursts
    noise.par.tx.expr      = "absTime.seconds * 0.05"
    noise.par.ty.expr      = "absTime.seconds * 0.03"

    # ── Color: shift hue with mid-band energy ─────────────────────────────────

    hsv = p.create(hsvAdjustTOP, 'hsv_color')
    hsv.nodeX, hsv.nodeY = 0, 400
    # Slowly rotate hue over time + mid band adds fast color shifts
    hsv.par.hue.expr        = "absTime.seconds * 0.04 % 1.0 + op('data_mid')['chan1'] * 0.3"
    hsv.par.saturation.expr = "0.6 + op('data_mid')['chan1'] * 0.4"
    hsv.par.value.expr      = "0.5 + op('data_bass')['chan1'] * 0.5"
    hsv.setInput(0, noise)

    # ── Feedback trail ────────────────────────────────────────────────────────
    # The Feedback TOP reads the OUTPUT from the PREVIOUS frame.
    # We composite the new noise over a slightly faded version of history.
    # This creates luminous trails that fade proportionally to the gap between beats.

    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = -200, 200
    # feedback.par.target is set after 'comp_feedback' is created (see below)

    # Slightly darken the feedback each frame so old frames fade out
    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = 0, 200
    # When bass hits, slow the fade (trails linger); silence = quick fade
    fade.par.brightness.expr = "0.88 + op('data_bass')['chan1'] * 0.10"
    fade.setInput(0, feedback)

    # Blend new frame (add) over the faded history
    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 200, 400
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)        # faded history
    comp_fb.setInput(1, hsv)         # new noise frame

    # Point the feedback TOP at the composite output to close the loop
    feedback.par.top = comp_fb.name

    # Clamp so accumulated brightness doesn't blow out
    level_out = p.create(levelTOP, 'level_output')
    level_out.nodeX, level_out.nodeY = 400, 400
    level_out.par.opacity = 1.0
    level_out.par.gamma   = 0.9
    level_out.setInput(0, comp_fb)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 600, 400
    output.setInput(0, level_out)

    print("✓  Network 03 built.")
    print("   Bass controls zoom, mids control color/energy, highs add shimmer.")
    print("   TIP: Increase math_bass/mid/high 'Gain' if your signal is quiet.")

build()
