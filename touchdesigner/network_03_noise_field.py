"""
Network 03: Audio-Reactive Noise Field with Feedback
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

THREE-BAND CONTROL via direct spectrum bin indexing:
  Bass  (bins 1–4,   ~86–344 Hz)   → Noise period (zoom scale)
  Mid   (bins 15–35, ~1290–3010 Hz) → Amplitude + hue rotation
  High  (bins 60–120, ~5160–10320 Hz) → Roughness / texture detail

HOW FEEDBACK WORKS:
  The Feedback TOP reads the previous composite frame.
  Each frame = new noise blended over a dimmed copy of history.
  Bass hits slow the dimming → trails linger. Silence = quick fade.
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

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = p.create(td_op('audiodevInCHOP'), 'audio_in')
    audio.nodeX, audio.nodeY = -900, 300

    spectrum = p.create(td_op('spectrumCHOP'), 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 300
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    # Null CHOP: stable reference for spectrum data.
    # Expressions use: op('spectrum_data')[binIndex]
    # Bin n ≈ n × 86 Hz  (44100 Hz / 512 FFT bins)
    spec_data = p.create(td_op('nullCHOP'), 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 300
    spec_data.setInput(0, spectrum)

    # ── Band expressions ──────────────────────────────────────────────────────
    # Inline expressions that compute energy per frequency band.
    # Each expression sums a few representative bins and scales up.
    # If response is too weak:  increase the × multiplier (60 → 120, etc.)
    # If response is too strong: decrease it, or lower the clamp maximum.

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Noise TOP ─────────────────────────────────────────────────────────────

    noise = p.create(td_op('noiseTOP'), 'noise_field')
    noise.nodeX, noise.nodeY = -300, 300
    noise.par.periodx.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.periody.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.amp.expr     = f"0.4 + ({MID})  * 1.2"
    noise.par.rough.expr   = f"0.4 + ({HIGH}) * 0.5"
    noise.par.tx.expr      = "absTime.seconds * 0.04"
    noise.par.ty.expr      = "absTime.seconds * 0.025"

    # ── HSV Adjust: colour shifts with mid band ────────────────────────────────

    hsv = p.create(td_op('hsvAdjustTOP'), 'hsv_color')
    hsv.nodeX, hsv.nodeY = -100, 300
    hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({MID}) * 0.4) % 1.0"
    hsv.par.saturation.expr = f"0.7 + ({MID})  * 0.5"
    hsv.par.value.expr      = f"0.5 + ({BASS}) * 0.5"
    hsv.setInput(0, noise)

    # ── Feedback loop ─────────────────────────────────────────────────────────

    feedback = p.create(td_op('feedbackTOP'), 'feedback')
    feedback.nodeX, feedback.nodeY = -300, 100

    fade = p.create(td_op('levelTOP'), 'feedback_fade')
    fade.nodeX, fade.nodeY = -100, 100
    # 0.82 = moderate trail. Raise toward 0.97 for longer trails.
    fade.par.brightness.expr = f"0.82 + ({BASS}) * 0.15"
    fade.setInput(0, feedback)

    comp_fb = p.create(td_op('compositeTOP'), 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 100, 300
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)    # faded history (behind)
    comp_fb.setInput(1, hsv)     # new frame (on top)

    # Close the loop: Feedback TOP reads from comp_feedback
    feedback.par.top = comp_fb.name

    level_out = p.create(td_op('levelTOP'), 'level_output')
    level_out.nodeX, level_out.nodeY = 300, 300
    level_out.par.gamma = 0.85   # prevent permanent blow-out from feedback
    level_out.setInput(0, comp_fb)

    output = p.create(td_op('nullTOP'), 'OUTPUT')
    output.nodeX, output.nodeY = 500, 300
    output.setInput(0, level_out)

    print("=" * 55)
    print("Network 03: Noise Field + Feedback — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ Bass:  zoom / scale of noise blobs")
    print("→ Mid:   hue rotation + colour intensity")
    print("→ High:  fine detail / texture speed")
    print("→ Tune multipliers (×60 / ×90 / ×120) in the")
    print("  BASS/MID/HIGH expressions inside noise_field")
    print("=" * 55)


build()
