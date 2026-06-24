"""
Network 03: Audio-Reactive Noise Field with Feedback
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.

THREE-BAND CONTROL:
  Bass  (bins 1–4)   → Noise zoom / period
  Mid   (bins 15–35) → Amplitude + hue rotation
  High  (bins 60–120) → Roughness / texture speed
"""

import builtins as _bt
try:
    import td as _td
except Exception:
    _td = None


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
    audio.nodeX, audio.nodeY = -900, 300

    spectrum = create_op(p, 'spectrumCHOP', 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 300
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    # Null CHOP: reference point for spectrum data.
    # Expressions use op('spectrum_data')[binIndex]  (0-indexed).
    # With 44100 Hz / 512 FFT: bin n ≈ n × 86 Hz.
    spec_data = create_op(p, 'nullCHOP', 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 300
    spec_data.setInput(0, spectrum)

    # ── Band expressions ──────────────────────────────────────────────────────
    # Tune the × multipliers if response is too weak or too strong.

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Noise TOP ─────────────────────────────────────────────────────────────

    noise = create_op(p, 'noiseTOP', 'noise_field')
    noise.nodeX, noise.nodeY = -300, 300
    noise.par.periodx.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.periody.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.amp.expr     = f"0.4 + ({MID})  * 1.2"
    noise.par.rough.expr   = f"0.4 + ({HIGH}) * 0.5"
    noise.par.tx.expr      = "absTime.seconds * 0.04"
    noise.par.ty.expr      = "absTime.seconds * 0.025"

    # ── HSV Adjust: hue follows mid band ─────────────────────────────────────

    hsv = create_op(p, 'hsvAdjustTOP', 'hsv_color')
    hsv.nodeX, hsv.nodeY = -100, 300
    hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({MID}) * 0.4) % 1.0"
    hsv.par.saturation.expr = f"0.7 + ({MID})  * 0.5"
    hsv.par.value.expr      = f"0.5 + ({BASS}) * 0.5"
    hsv.setInput(0, noise)

    # ── Feedback loop ─────────────────────────────────────────────────────────

    feedback = create_op(p, 'feedbackTOP', 'feedback')
    feedback.nodeX, feedback.nodeY = -300, 100

    # 0.82 = moderate trail. Raise toward 0.97 for longer trails.
    fade = create_op(p, 'levelTOP', 'feedback_fade')
    fade.nodeX, fade.nodeY = -100, 100
    fade.par.brightness.expr = f"0.82 + ({BASS}) * 0.15"
    fade.setInput(0, feedback)

    comp_fb = create_op(p, 'compositeTOP', 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 100, 300
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, hsv)
    feedback.par.top = comp_fb.name

    level_out = create_op(p, 'levelTOP', 'level_output')
    level_out.nodeX, level_out.nodeY = 300, 300
    level_out.par.gamma = 0.85
    level_out.setInput(0, comp_fb)

    output = create_op(p, 'nullTOP', 'OUTPUT')
    output.nodeX, output.nodeY = 500, 300
    output.setInput(0, level_out)

    print("=" * 55)
    print("Network 03: Noise Field + Feedback — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ Bass: zoom/scale    Mid: hue    High: texture speed")
    print("→ Tune ×60/×90/×120 multipliers in noise_field expressions")
    print("=" * 55)


build()
