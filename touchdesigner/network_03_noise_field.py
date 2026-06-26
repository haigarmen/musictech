"""
Network 03: Audio-Reactive Noise Field with Feedback
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.

AUDIO CONTROL:
  Overall energy drives all three effects via RMS analysis (same method as
  Network 01, confirmed working). Period, amplitude and roughness all respond
  to loudness — bass hits make the noise zoom and trails grow.
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

    # ── Audio analysis — RMS (same pattern as Network 01, confirmed working) ───
    # op('rms_data')[0]  →  0.0 (silence) … 1.0 (loud)

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP')
    audio.nodeX, audio.nodeY = -900, 300

    rms = create_op(p, 'analyze_rms', 'analyzeCHOP')
    rms.nodeX, rms.nodeY = -700, 300
    rms.par.function = 'rms'
    connect_op(rms, 0, audio)

    rms_gain = create_op(p, 'rms_gain', 'mathCHOP')
    rms_gain.nodeX, rms_gain.nodeY = -500, 300
    rms_gain.par.gain = 8.0    # raise if noise barely moves; lower if it maxes out
    connect_op(rms_gain, 0, rms)

    rms_data = create_op(p, 'rms_data', 'nullCHOP')
    rms_data.nodeX, rms_data.nodeY = -300, 300
    connect_op(rms_data, 0, rms_gain)

    # Single expression reference — op('rms_data')[0] is a plain float, always safe
    E = "min(1.0, max(0.0, op('rms_data')[0]))"

    # ── Noise TOP ─────────────────────────────────────────────────────────────

    noise = create_op(p, 'noise_field', 'noiseTOP')
    noise.nodeX, noise.nodeY = -100, 300
    noise.par.period.expr = f"0.2 + ({E}) * 1.5"
    for _ap in ('amp', 'amplitude'):
        try:
            getattr(noise.par, _ap).expr = f"0.4 + ({E}) * 1.2"
            break
        except AttributeError:
            continue
    noise.par.rough.expr = f"0.4 + ({E}) * 0.5"
    noise.par.tx.expr    = "absTime.seconds * 0.04"
    noise.par.ty.expr    = "absTime.seconds * 0.025"

    # ── HSV colour (gracefully skipped if unavailable in this build) ──────────

    prev_top = noise
    hsv = try_create(p, 'hsv_color', 'hsvAdjustTOP')
    if hsv is not None:
        hsv.nodeX, hsv.nodeY = 100, 300
        try:
            hsv.par.hue.expr        = f"(absTime.seconds * 0.05 + ({E}) * 0.4) % 1.0"
            hsv.par.saturation.expr = f"0.7 + ({E}) * 0.5"
            hsv.par.value.expr      = f"0.5 + ({E}) * 0.5"
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
    fade.par.brightness1.expr = f"0.82 + ({E}) * 0.15"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 300, 300
    comp_fb.par.operand = 'add'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, prev_top)
    feedback.par.top = comp_fb.name

    level_out = create_op(p, 'level_output', 'levelTOP')
    level_out.nodeX, level_out.nodeY = 500, 300
    level_out.par.gamma1 = 0.85
    connect_op(level_out, 0, comp_fb)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 700, 300
    connect_op(output, 0, level_out)

    print("=" * 55)
    print("Network 03: Noise Field + Feedback — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Not moving: select rms_gain, raise Gain (try 20–50)")
    print("→ Longer trails: select feedback_fade, raise Brightness1")
    print("=" * 55)


build()
