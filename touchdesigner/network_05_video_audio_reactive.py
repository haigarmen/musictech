"""
Network 05: Real-Time Video Source Altered by Audio
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  After building: select 'video_in' → Parameters → set Device to your webcam.

THREE-BAND EFFECTS:
  BASS  → Feedback depth   (ghost trails on kick/bass hits)
  MID   → Hue rotation     (colour shifts on melody)
  HIGH  → Pixel ripple     (displacement jitter on transients)
"""

VIDEO_DEVICE_INDEX = 0    # 0 = first camera. Change if needed.


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
    audio.nodeX, audio.nodeY = -1000, 500

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -800, 500
    spectrum.par.fftsize = 512
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -600, 500
    connect_op(spec_data, 0, spectrum)

    # spectrum_data has 1 channel; frequency bins are samples: [0][bin_index]
    BASS = "min(1.0, max(0.0, (op('spectrum_data')[0][1]+op('spectrum_data')[0][2]+op('spectrum_data')[0][3]+op('spectrum_data')[0][4])*60))"
    MID  = "min(1.0, max(0.0, (op('spectrum_data')[0][15]+op('spectrum_data')[0][25]+op('spectrum_data')[0][35])*90))"
    HIGH = "min(1.0, max(0.0, (op('spectrum_data')[0][60]+op('spectrum_data')[0][90]+op('spectrum_data')[0][120])*120))"

    # ── Live video ────────────────────────────────────────────────────────────

    vid = create_op(p, 'video_in', 'videodeviceinTOP')
    vid.nodeX, vid.nodeY = -600, 100
    for _dp in ('device', 'deviceindex', 'devicenum'):
        try:
            getattr(vid.par, _dp).val = VIDEO_DEVICE_INDEX
            break
        except AttributeError:
            continue

    # ── Effect 1: Displacement (HIGH) ────────────────────────────────────────

    disp_noise = create_op(p, 'disp_noise', 'noiseTOP')
    disp_noise.nodeX, disp_noise.nodeY = -600, -100
    disp_noise.par.tx.expr    = "absTime.seconds * 0.15"
    disp_noise.par.ty.expr    = "absTime.seconds * 0.09"
    disp_noise.par.rough.expr = f"0.5 + ({HIGH}) * 0.45"

    displace = create_op(p, 'displace_high', 'displaceTOP')
    displace.nodeX, displace.nodeY = -400, 100
    # TD 2025: displaceweightx / displaceweighty (not displacex / displacey)
    displace.par.displaceweightx.expr = f"0.003 + ({HIGH}) * 0.06"
    displace.par.displaceweighty.expr = f"0.003 + ({HIGH}) * 0.04"
    connect_op(displace, 0, vid)
    connect_op(displace, 1, disp_noise)

    # ── Effect 2: Hue rotation (MID, gracefully skipped if unavailable) ───────

    prev_top = displace
    hsv = try_create(p, 'hsv_shift', 'hsvAdjustTOP')
    if hsv is not None:
        hsv.nodeX, hsv.nodeY = -200, 100
        try:
            hsv.par.hue.expr        = f"(absTime.seconds * 0.02 + ({MID}) * 0.5) % 1.0"
            hsv.par.saturation.expr = f"1.0 + ({MID}) * 0.9"
            hsv.par.value.expr      = f"0.85 + ({BASS}) * 0.3"
        except AttributeError:
            pass
        connect_op(hsv, 0, displace)
        prev_top = hsv

    # ── Effect 3: Feedback trail (BASS) ──────────────────────────────────────

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = -200, -100

    # 0.60 = fast decay (crisp). 0.94 = slow decay (heavy trails).
    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = 0, -100
    fade.par.brightness1.expr = f"0.60 + ({BASS}) * 0.34"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 0, 100
    comp_fb.par.operand = 'over'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, prev_top)
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    post_top = comp_fb

    glow = try_create(p, 'glow', 'glowTOP')
    if glow is not None:
        glow.nodeX, glow.nodeY = 200, 100
        try:
            glow.par.size.expr     = f"1 + ({BASS}) * 25"
            glow.par.strength.expr = f"0.05 + ({BASS}) * 0.7"
        except AttributeError:
            pass
        connect_op(glow, 0, comp_fb)
        post_top = glow

    level_out = create_op(p, 'level_output', 'levelTOP')
    level_out.nodeX, level_out.nodeY = 400, 100
    # TD 2025: contrast1 / gamma1 (not contrast / gamma)
    for _cp in ('contrast1', 'contrast'):
        try:
            getattr(level_out.par, _cp).val = 1.1
            break
        except AttributeError:
            continue
    level_out.par.gamma1 = 0.9
    connect_op(level_out, 0, post_top)

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
