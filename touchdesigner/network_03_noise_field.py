"""
Network 03: Audio-Reactive Noise Field with Feedback
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.

THREE-BAND CONTROL:
  Bass  (bins 1–4)    → Noise zoom / period
  Mid   (bins 15–35)  → Amplitude + hue rotation
  High  (bins 60–120) → Roughness / texture speed
"""


def create_op(parent_comp, node_name, *type_names):
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
    raise RuntimeError(f"Cannot create '{node_name}'. Tried: {attempts}")


def try_create(parent_comp, node_name, *type_names):
    """Returns None instead of raising if the operator type doesn't exist."""
    try:
        return create_op(parent_comp, node_name, *type_names)
    except RuntimeError:
        print(f"  Note: '{node_name}' skipped — none of {type_names} exist in this TD build.")
        return None


def connect_op(dest, index, source):
    """Wire source → dest via inputConnectors; falls back to par.chop/top reference."""
    try:
        dest.inputConnectors[index].connect(source)
        return
    except (AttributeError, IndexError):
        pass
    if index == 0:
        for _pn in ('chop', 'top', 'choppath', 'toppath'):
            try:
                getattr(dest.par, _pn).val = source.path
                return
            except AttributeError:
                continue
    print(f"  Warning: could not connect {source.name} → {dest.name}[{index}]")


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP')
    audio.nodeX, audio.nodeY = -900, 300

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 300
    spectrum.par.fftsize = 512
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 300
    connect_op(spec_data, 0, spectrum)

    BASS = "min(1.0, max(0.0, (op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60))"
    MID  = "min(1.0, max(0.0, (op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90))"
    HIGH = "min(1.0, max(0.0, (op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120))"

    # ── Noise TOP ─────────────────────────────────────────────────────────────

    noise = create_op(p, 'noise_field', 'noiseTOP')
    noise.nodeX, noise.nodeY = -300, 300
    # TD 2025: single 'period' param (not periodx / periody)
    noise.par.period.expr = f"0.2 + ({BASS}) * 1.5"
    for _ap in ('amp', 'amplitude'):
        try:
            getattr(noise.par, _ap).expr = f"0.4 + ({MID}) * 1.2"
            break
        except AttributeError:
            continue
    noise.par.rough.expr = f"0.4 + ({HIGH}) * 0.5"
    noise.par.tx.expr    = "absTime.seconds * 0.04"
    noise.par.ty.expr    = "absTime.seconds * 0.025"

    # ── HSV colour (gracefully skipped if unavailable in this build) ──────────

    prev_top = noise
    hsv = try_create(p, 'hsv_color', 'hsvAdjustTOP')
    if hsv is not None:
        hsv.nodeX, hsv.nodeY = -100, 300
        try:
            hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({MID}) * 0.4) % 1.0"
            hsv.par.saturation.expr = f"0.7 + ({MID}) * 0.5"
            hsv.par.value.expr      = f"0.5 + ({BASS}) * 0.5"
        except AttributeError:
            pass
        connect_op(hsv, 0, noise)
        prev_top = hsv

    # ── Feedback loop ─────────────────────────────────────────────────────────

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = -300, 100

    # 0.82 = moderate trail. Raise toward 0.97 for longer trails.
    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = -100, 100
    fade.par.brightness1.expr = f"0.82 + ({BASS}) * 0.15"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 100, 300
    comp_fb.par.operand = 'add'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, prev_top)
    feedback.par.top = comp_fb.name

    level_out = create_op(p, 'level_output', 'levelTOP')
    level_out.nodeX, level_out.nodeY = 300, 300
    level_out.par.gamma1 = 0.85
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
