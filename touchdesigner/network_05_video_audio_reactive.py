"""
Network 05: Real-Time Video Source Altered by Audio
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.
  Connect your webcam before running.

AFTER BUILDING:
  Select 'video_in' → Parameters → set Device to your camera index.
  Right-click OUTPUT → View.

THREE-BAND EFFECTS:
  BASS  → Feedback depth   (kick drum = smear / ghost trails)
  MID   → Hue rotation     (melody = colour palette shifting)
  HIGH  → Pixel ripple     (hi-hats / transients = displacement jitter)

NO WEBCAM? Replace 'video_in' after building:
  Delete it, add a Movie File In TOP named 'video_in', point at a video file.
"""

VIDEO_DEVICE_INDEX = 0    # 0 = first camera. Change if needed.


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
    print(f"Run in Textport: [x for x in dir() if x.endswith('TOP')]")
    print(f"Sample CHOPs: {chops[:6]}  Sample TOPs: {tops[:6]}")
    raise NameError(f"TD types not found: {names}")


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = p.create(td_op('audiodevInCHOP'), 'audio_in')
    audio.nodeX, audio.nodeY = -1000, 500

    spectrum = p.create(td_op('spectrumCHOP'), 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -800, 500
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = p.create(td_op('nullCHOP'), 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -600, 500
    spec_data.setInput(0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Live video source ─────────────────────────────────────────────────────

    vid = p.create(td_op('videodevInTOP'), 'video_in')
    vid.nodeX, vid.nodeY = -600, 100
    vid.par.device = VIDEO_DEVICE_INDEX

    # ── Effect 1: Pixel displacement (HIGH band) ──────────────────────────────
    # A noise texture acts as a displacement map.
    # High-frequency transients (hi-hats, claps) increase displacement,
    # causing the video to ripple and jitter.

    disp_noise = p.create(td_op('noiseTOP'), 'disp_noise')
    disp_noise.nodeX, disp_noise.nodeY = -600, -100
    disp_noise.par.tx.expr    = "absTime.seconds * 0.15"
    disp_noise.par.ty.expr    = "absTime.seconds * 0.09"
    disp_noise.par.rough.expr = f"0.5 + ({HIGH}) * 0.45"

    displace = p.create(td_op('displaceTOP'), 'displace_high')
    displace.nodeX, displace.nodeY = -400, 100
    displace.par.displacex.expr = f"0.003 + ({HIGH}) * 0.06"
    displace.par.displacey.expr = f"0.003 + ({HIGH}) * 0.04"
    displace.setInput(0, vid)          # image to warp
    displace.setInput(1, disp_noise)   # displacement map

    # ── Effect 2: Hue rotation (MID band) ────────────────────────────────────
    # Mid-range content (vocals, chords) rotates the colour palette.
    # At rest the video looks near-natural; on melodic hits it shifts colour.

    hsv = p.create(td_op('hsvAdjustTOP'), 'hsv_shift')
    hsv.nodeX, hsv.nodeY = -200, 100
    hsv.par.hue.expr        = f"(absTime.seconds * 0.02 + ({MID}) * 0.5) % 1.0"
    hsv.par.saturation.expr = f"1.0 + ({MID}) * 0.9"
    hsv.par.value.expr      = f"0.85 + ({BASS}) * 0.3"
    hsv.setInput(0, displace)

    # ── Effect 3: Feedback trail (BASS band) ──────────────────────────────────
    # Previous frames linger as ghost images proportional to bass energy.
    # Kick drums and bass hits push the fade factor near 1.0 = long smear.
    # Silence keeps it at 0.60 = crisp, fast decay.

    feedback = p.create(td_op('feedbackTOP'), 'feedback')
    feedback.nodeX, feedback.nodeY = -200, -100

    fade = p.create(td_op('levelTOP'), 'feedback_fade')
    fade.nodeX, fade.nodeY = 0, -100
    fade.par.brightness.expr = f"0.60 + ({BASS}) * 0.34"
    fade.setInput(0, feedback)

    # 'over' keeps the video readable.
    # Try 'add' for a bright accumulating glow effect instead.
    comp_fb = p.create(td_op('compositeTOP'), 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 0, 100
    comp_fb.par.operand = 'over'
    comp_fb.setInput(0, fade)   # faded history behind
    comp_fb.setInput(1, hsv)    # current frame in front
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = p.create(td_op('glowTOP'), 'glow')
    glow.nodeX, glow.nodeY = 200, 100
    glow.par.size.expr     = f"1 + ({BASS}) * 25"
    glow.par.strength.expr = f"0.05 + ({BASS}) * 0.7"
    glow.setInput(0, comp_fb)

    level_out = p.create(td_op('levelTOP'), 'level_output')
    level_out.nodeX, level_out.nodeY = 400, 100
    level_out.par.contrast = 1.1
    level_out.par.gamma    = 0.9
    level_out.setInput(0, glow)

    output = p.create(td_op('nullTOP'), 'OUTPUT')
    output.nodeX, output.nodeY = 600, 100
    output.setInput(0, level_out)

    print("=" * 55)
    print("Network 05: Video + Audio — BUILT in", p.path)
    print()
    print("SETUP:")
    print("  1. Select 'video_in' → set Device to your webcam")
    print("  2. Right-click OUTPUT → View")
    print()
    print("WHAT TO LISTEN FOR:")
    print("  BASS  → ghost trails on the video image")
    print("  MID   → colour palette rotating through hues")
    print("  HIGH  → image ripples and pixel jitter")
    print()
    print("QUICK TUNING:")
    print("  More reaction → raise ×60/×90/×120 multipliers in")
    print("  the BASS/MID/HIGH expressions on spectrum_data")
    print("  Longer trails → raise feedback_fade brightness upper bound")
    print("=" * 55)


build()
