"""
Network 03: Audio-Reactive Noise Field with Feedback Trail
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

WHAT GETS BUILT:
  Audio In → Spectrum CHOP → spectrum_data (Null CHOP)
  Spectrum bin expressions drive Noise TOP → HSV Adjust → Composite + Feedback loop
  → Level → Null TOP (OUTPUT)

THREE-BAND CONTROL (using direct spectrum bin indexing):
  Bass  (bins  0–5,  ~0–430 Hz)  → Noise period (zoom level of texture)
  Mid   (bins 15–40, ~1300–3440 Hz) → Amplitude + hue rotation
  High  (bins 60–120, ~5160–10320 Hz) → Roughness (texture detail / speed)

HOW THE FEEDBACK LOOP WORKS:
  The Feedback TOP reads the PREVIOUS frame's composite output.
  Each frame = new noise layer blended over a slightly darkened copy of history.
  On bass hits the history fades slowly (long trails). In silence it fades quickly.

TROUBLESHOOTING:
  • Nothing visible: the Noise TOP's 'amp' expression may evaluate to 0.
    Hardcode amp=1.0 temporarily on the Noise TOP to verify the visual chain works,
    then re-enable the expression.
  • Feedback not working: the Feedback TOP needs its 'Target TOP' parameter set
    to the name of the composite node ('comp_feedback'). Verify this in its params.
  • Colors not shifting: select 'hsv_color' and temporarily set Hue to a non-zero
    static value to confirm the HSV Adjust is connected correctly.
"""


def build():
    p = me.parent()

    # ── Audio + spectrum ──────────────────────────────────────────────────────

    audio = p.create(audiodevInCHOP, 'audio_in')
    audio.nodeX, audio.nodeY = -900, 200

    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 200
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    # Null CHOP: stable tap point for spectrum data.
    # Expressions reference specific bins: op('spectrum_data')[binIndex]
    # Bin n ≈ n × 86 Hz  (for 44100 Hz sample rate / 512-point FFT)
    spec_data = p.create(nullCHOP, 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 200
    spec_data.setInput(0, spectrum)

    # ── Helper expressions ────────────────────────────────────────────────────
    # These inline expressions compute band energy from spectrum bins.
    # The gain multipliers (×60, ×90, ×120) amplify the tiny FFT values.
    # If response is too weak, increase these multipliers.
    # If response is too wild, decrease them.

    BASS  = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4]) * 60, 0, 1)"
    MID   = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35]) * 90, 0, 1)"
    HIGH  = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120]) * 120, 0, 1)"

    # ── Noise TOP: procedural animated texture ────────────────────────────────

    noise = p.create(noiseTOP, 'noise_field')
    noise.nodeX, noise.nodeY = -300, 200
    # period: controls the scale of noise features.
    # Bass lifts period → large blobs pulse with kick drum.
    noise.par.periodx.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.periody.expr = f"0.2 + ({BASS}) * 1.5"
    # amp: overall noise brightness. Mid energy drives intensity.
    noise.par.amp.expr     = f"0.4 + ({MID}) * 1.2"
    # roughness: detail level. High frequencies add fine, fast detail.
    noise.par.rough.expr   = f"0.4 + ({HIGH}) * 0.5"
    # Slow drift so the texture crawls even in silence.
    noise.par.tx.expr = "absTime.seconds * 0.04"
    noise.par.ty.expr = "absTime.seconds * 0.025"

    # ── HSV Adjust: hue follows time + mid frequencies ────────────────────────

    hsv = p.create(hsvAdjustTOP, 'hsv_color')
    hsv.nodeX, hsv.nodeY = -100, 200
    # Hue slowly rotates; mid energy jumps it further for color bursts.
    hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({MID}) * 0.4) % 1.0"
    hsv.par.saturation.expr = f"0.7 + ({MID}) * 0.5"
    hsv.par.value.expr      = f"0.5 + ({BASS}) * 0.5"
    hsv.setInput(0, noise)

    # ── Feedback loop ─────────────────────────────────────────────────────────
    # Feedback TOP: reads the previous frame from comp_feedback (set below).
    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = -300, 0

    # Darken history each frame. Bass hits slow the fade → trails linger longer.
    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = -100, 0
    fade.par.brightness.expr = f"0.82 + ({BASS}) * 0.15"
    fade.setInput(0, feedback)

    # Blend new noise frame (add) over faded history.
    # Add blend makes bright areas accumulate — lush glow on loud moments.
    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 100, 200
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)    # faded history
    comp_fb.setInput(1, hsv)     # current frame

    # Point the Feedback TOP at comp_feedback to close the loop.
    # On the Feedback TOP, the 'Target TOP' parameter must name this node.
    feedback.par.top = comp_fb.name

    # ── Output ────────────────────────────────────────────────────────────────

    # Clamp accumulated brightness so it doesn't permanently blow out.
    level_out = p.create(levelTOP, 'level_output')
    level_out.nodeX, level_out.nodeY = 300, 200
    level_out.par.gamma = 0.85
    level_out.setInput(0, comp_fb)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 500, 200
    output.setInput(0, level_out)

    print("=" * 50)
    print("Network 03: Noise Field with Feedback — BUILT")
    print("Container:", p.path)
    print()
    print("What to tune:")
    print("  Bass multiplier (×60 in BASS expression) → zoom reaction depth")
    print("  Mid multiplier  (×90 in MID expression)  → color shift intensity")
    print("  High multiplier (×120 in HIGH expression) → texture detail speed")
    print("  feedback_fade brightness expression upper bound (~0.97) → trail length")
    print()
    print("Right-click OUTPUT → View")
    print("=" * 50)


build()
