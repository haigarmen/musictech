"""
Network 05: Real-Time Video Source Altered by Audio
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.
  After building: select 'video_in' → Parameters → set Device to your webcam.

THREE-BAND EFFECTS:
  BASS  → Feedback depth   (ghost trails on kick/bass hits)
  MID   → Hue rotation     (colour shifts on melody)
  HIGH  → Pixel ripple     (displacement jitter on transients)
"""

import builtins as _bt
try:
    import td as _td
except Exception:
    _td = None

VIDEO_DEVICE_INDEX = 0    # 0 = first camera. Change if needed.


def td_op(*names):
    g = globals()
    for name in names:
        t = g.get(name)
        if t is not None:
            return t
        t = getattr(_bt, name, None)
        if t is not None:
            return t
        if _td is not None:
            t = getattr(_td, name, None)
            if t is not None:
                return t
    return names[0]


def create_op(parent_comp, type_name, node_name):
    op_type = td_op(type_name)
    if not isinstance(op_type, str):
        try:
            return parent_comp.create(op_type, node_name)
        except Exception:
            pass
    short = type_name
    for suffix in ('CHOP', 'TOP', 'SOP', 'COMP', 'MAT', 'DAT'):
        if type_name.endswith(suffix):
            short = type_name[:-len(suffix)]
            break
    for attempt in (short, type_name):
        try:
            n = parent_comp.create(attempt, node_name)
            if n is not None:
                return n
        except Exception:
            pass
    raise RuntimeError(
        f"Cannot create '{type_name}'. Add manually: right-click → Add Operator,"
        f" search '{short}', rename to '{node_name}'. Run diagnose.py for help."
    )


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audiodevInCHOP', 'audio_in')
    audio.nodeX, audio.nodeY = -1000, 500

    spectrum = create_op(p, 'spectrumCHOP', 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -800, 500
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = create_op(p, 'nullCHOP', 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -600, 500
    spec_data.setInput(0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Live video ────────────────────────────────────────────────────────────

    vid = create_op(p, 'videodevInTOP', 'video_in')
    vid.nodeX, vid.nodeY = -600, 100
    vid.par.device = VIDEO_DEVICE_INDEX

    # ── Effect 1: Displacement (HIGH) ─────────────────────────────────────────

    disp_noise = create_op(p, 'noiseTOP', 'disp_noise')
    disp_noise.nodeX, disp_noise.nodeY = -600, -100
    disp_noise.par.tx.expr    = "absTime.seconds * 0.15"
    disp_noise.par.ty.expr    = "absTime.seconds * 0.09"
    disp_noise.par.rough.expr = f"0.5 + ({HIGH}) * 0.45"

    displace = create_op(p, 'displaceTOP', 'displace_high')
    displace.nodeX, displace.nodeY = -400, 100
    displace.par.displacex.expr = f"0.003 + ({HIGH}) * 0.06"
    displace.par.displacey.expr = f"0.003 + ({HIGH}) * 0.04"
    displace.setInput(0, vid)
    displace.setInput(1, disp_noise)

    # ── Effect 2: Hue rotation (MID) ─────────────────────────────────────────

    hsv = create_op(p, 'hsvAdjustTOP', 'hsv_shift')
    hsv.nodeX, hsv.nodeY = -200, 100
    hsv.par.hue.expr        = f"(absTime.seconds * 0.02 + ({MID}) * 0.5) % 1.0"
    hsv.par.saturation.expr = f"1.0 + ({MID}) * 0.9"
    hsv.par.value.expr      = f"0.85 + ({BASS}) * 0.3"
    hsv.setInput(0, displace)

    # ── Effect 3: Feedback trail (BASS) ──────────────────────────────────────

    feedback = create_op(p, 'feedbackTOP', 'feedback')
    feedback.nodeX, feedback.nodeY = -200, -100

    # 0.60 = fast decay (crisp). 0.94 = slow decay (heavy trails).
    fade = create_op(p, 'levelTOP', 'feedback_fade')
    fade.nodeX, fade.nodeY = 0, -100
    fade.par.brightness.expr = f"0.60 + ({BASS}) * 0.34"
    fade.setInput(0, feedback)

    comp_fb = create_op(p, 'compositeTOP', 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 0, 100
    comp_fb.par.operand = 'over'   # try 'add' for bright accumulating glow
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, hsv)
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = create_op(p, 'glowTOP', 'glow')
    glow.nodeX, glow.nodeY = 200, 100
    glow.par.size.expr     = f"1 + ({BASS}) * 25"
    glow.par.strength.expr = f"0.05 + ({BASS}) * 0.7"
    glow.setInput(0, comp_fb)

    level_out = create_op(p, 'levelTOP', 'level_output')
    level_out.nodeX, level_out.nodeY = 400, 100
    level_out.par.contrast = 1.1
    level_out.par.gamma    = 0.9
    level_out.setInput(0, glow)

    output = create_op(p, 'nullTOP', 'OUTPUT')
    output.nodeX, output.nodeY = 600, 100
    output.setInput(0, level_out)

    print("=" * 55)
    print("Network 05: Video + Audio — BUILT in", p.path)
    print()
    print("SETUP: select 'video_in' → set Device to your webcam")
    print("→ Right-click OUTPUT → View")
    print()
    print("BASS → ghost trails   MID → colour shift   HIGH → pixel ripple")
    print("=" * 55)


build()
