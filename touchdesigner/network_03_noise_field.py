"""
Network 03: Audio-Reactive Noise Field with Feedback
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.

THREE-BAND CONTROL:
  Bass  (bins 1–4)    → Noise zoom / period
  Mid   (bins 15–35)  → Amplitude + hue rotation
  High  (bins 60–120) → Roughness / texture speed
"""


def create_op(parent_comp, node_name, *type_names):
    """
    Create a TD operator using string-based creation (confirmed working in TD 2025+).
    Tries each provided type name, then auto-tries an all-lowercase variant.
    """
    attempts = list(type_names)
    for name in type_names:
        for fam in ('CHOP', 'TOP', 'SOP', 'Comp', 'COMP', 'MAT', 'DAT'):
            if name.endswith(fam):
                lc = name[:-len(fam)].lower() + fam
                if lc not in attempts:
                    attempts.append(lc)
                break

    for name in attempts:
        try:
            n = parent_comp.create(name, node_name)
            if n is not None:
                return n
        except Exception:
            pass

    raise RuntimeError(
        f"Cannot create '{node_name}'. Tried: {attempts}\n"
        f"Add manually: right-click → Add Operator, search for the operator,\n"
        f"rename it to '{node_name}'. Run diagnose.py for environment info."
    )


def connect_op(dest, index, source):
    """Wire source → dest input slot, trying setInput then inputConnectors."""
    try:
        dest.setInput(index, source)
    except AttributeError:
        dest.inputConnectors[index].connect(source)


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP', 'audiodevInCHOP')
    audio.nodeX, audio.nodeY = -900, 300

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP', 'spectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 300
    for _wp in ('winsize', 'windowsize', 'fftsize', 'window'):
        try:
            getattr(spectrum.par, _wp).val = 512
            break
        except AttributeError:
            continue
    connect_op(spectrum, 0, audio)

    # Null CHOP: reference point for spectrum data.
    # Expressions use op('spectrum_data')[binIndex]  (0-indexed).
    # With 44100 Hz / 512 FFT: bin n ≈ n × 86 Hz.
    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 300
    connect_op(spec_data, 0, spectrum)

    # ── Band expressions ──────────────────────────────────────────────────────
    # Tune the × multipliers if response is too weak or too strong.

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Noise TOP ─────────────────────────────────────────────────────────────

    noise = create_op(p, 'noise_field', 'noiseTOP')
    noise.nodeX, noise.nodeY = -300, 300
    noise.par.periodx.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.periody.expr = f"0.2 + ({BASS}) * 1.5"
    noise.par.amp.expr     = f"0.4 + ({MID})  * 1.2"
    noise.par.rough.expr   = f"0.4 + ({HIGH}) * 0.5"
    noise.par.tx.expr      = "absTime.seconds * 0.04"
    noise.par.ty.expr      = "absTime.seconds * 0.025"

    # ── HSV Adjust: hue follows mid band ─────────────────────────────────────

    hsv = create_op(p, 'hsv_color', 'hsvAdjustTOP')
    hsv.nodeX, hsv.nodeY = -100, 300
    hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({MID}) * 0.4) % 1.0"
    hsv.par.saturation.expr = f"0.7 + ({MID})  * 0.5"
    hsv.par.value.expr      = f"0.5 + ({BASS}) * 0.5"
    connect_op(hsv, 0, noise)

    # ── Feedback loop ─────────────────────────────────────────────────────────

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = -300, 100

    # 0.82 = moderate trail. Raise toward 0.97 for longer trails.
    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = -100, 100
    fade.par.brightness.expr = f"0.82 + ({BASS}) * 0.15"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 100, 300
    comp_fb.par.operand = 'add'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, hsv)
    feedback.par.top = comp_fb.name

    level_out = create_op(p, 'level_output', 'levelTOP')
    level_out.nodeX, level_out.nodeY = 300, 300
    level_out.par.gamma = 0.85
    connect_op(level_out, 0, comp_fb)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 500, 300
    connect_op(output, 0, level_out)

    print("=" * 55)
    print("Network 03: Noise Field + Feedback — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Bass: zoom/scale    Mid: hue    High: texture speed")
    print("→ Tune ×60/×90/×120 multipliers in noise_field expressions")
    print("=" * 55)


build()
