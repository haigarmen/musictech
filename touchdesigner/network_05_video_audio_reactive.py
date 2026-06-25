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

VIDEO_DEVICE_INDEX = 0    # 0 = first camera. Change if needed.


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
    audio.nodeX, audio.nodeY = -1000, 500

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP', 'spectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -800, 500
    for _wp in ('winsize', 'windowsize', 'fftsize', 'window'):
        try:
            getattr(spectrum.par, _wp).val = 512
            break
        except AttributeError:
            continue
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -600, 500
    connect_op(spec_data, 0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Live video ────────────────────────────────────────────────────────────

    vid = create_op(p, 'video_in', 'videodeviceinTOP', 'videodevInTOP')
    vid.nodeX, vid.nodeY = -600, 100
    vid.par.device = VIDEO_DEVICE_INDEX

    # ── Effect 1: Displacement (HIGH) ─────────────────────────────────────────

    disp_noise = create_op(p, 'disp_noise', 'noiseTOP')
    disp_noise.nodeX, disp_noise.nodeY = -600, -100
    disp_noise.par.tx.expr    = "absTime.seconds * 0.15"
    disp_noise.par.ty.expr    = "absTime.seconds * 0.09"
    disp_noise.par.rough.expr = f"0.5 + ({HIGH}) * 0.45"

    displace = create_op(p, 'displace_high', 'displaceTOP')
    displace.nodeX, displace.nodeY = -400, 100
    displace.par.displacex.expr = f"0.003 + ({HIGH}) * 0.06"
    displace.par.displacey.expr = f"0.003 + ({HIGH}) * 0.04"
    connect_op(displace, 0, vid)
    connect_op(displace, 1, disp_noise)

    # ── Effect 2: Hue rotation (MID) ─────────────────────────────────────────

    hsv = create_op(p, 'hsv_shift', 'hsvAdjustTOP')
    hsv.nodeX, hsv.nodeY = -200, 100
    hsv.par.hue.expr        = f"(absTime.seconds * 0.02 + ({MID}) * 0.5) % 1.0"
    hsv.par.saturation.expr = f"1.0 + ({MID}) * 0.9"
    hsv.par.value.expr      = f"0.85 + ({BASS}) * 0.3"
    connect_op(hsv, 0, displace)

    # ── Effect 3: Feedback trail (BASS) ──────────────────────────────────────

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = -200, -100

    # 0.60 = fast decay (crisp). 0.94 = slow decay (heavy trails).
    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = 0, -100
    fade.par.brightness.expr = f"0.60 + ({BASS}) * 0.34"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 0, 100
    comp_fb.par.operand = 'over'   # try 'add' for bright accumulating glow
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, hsv)
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = create_op(p, 'glow', 'glowTOP')
    glow.nodeX, glow.nodeY = 200, 100
    glow.par.size.expr     = f"1 + ({BASS}) * 25"
    glow.par.strength.expr = f"0.05 + ({BASS}) * 0.7"
    connect_op(glow, 0, comp_fb)

    level_out = create_op(p, 'level_output', 'levelTOP')
    level_out.nodeX, level_out.nodeY = 400, 100
    level_out.par.contrast = 1.1
    level_out.par.gamma    = 0.9
    connect_op(level_out, 0, glow)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 600, 100
    connect_op(output, 0, level_out)

    print("=" * 55)
    print("Network 05: Video + Audio — BUILT in", p.path)
    print()
    print("SETUP: select 'video_in' → set Device to your webcam")
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print()
    print("BASS → ghost trails   MID → colour shift   HIGH → pixel ripple")
    print("=" * 55)


build()
