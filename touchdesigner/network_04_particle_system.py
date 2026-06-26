"""
Network 04: 3D Audio-Reactive Particle System
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.

AFTER BUILDING — REQUIRED MANUAL STEP:
  Select 'particle_geo' → Parameters → Render tab → set Material to 'phong_mat'.

THREE-BAND CONTROL:
  Bass  → birth rate    Mid  → velocity + colour    High → turbulence
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
    """Wire source → dest, trying setInput, inputConnectors, then par reference."""
    try:
        dest.setInput(index, source)
        return
    except AttributeError:
        pass
    try:
        dest.inputConnectors[index].connect(source)
        return
    except (AttributeError, IndexError):
        pass
    # Operators like choptoTOP/audiospectrumCHOP use a parameter reference
    candidates = ('chop', 'top', 'choppath', 'toppath') if index == 0 else ('chop2', 'top2')
    for par_name in candidates:
        try:
            getattr(dest.par, par_name).val = source.path
            return
        except AttributeError:
            continue
    print(f"  Warning: could not connect {source.name} to {dest.name}[{index}]")


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP', 'audiodevInCHOP')
    audio.nodeX, audio.nodeY = -900, 500

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP', 'spectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 500
    for _wp in ('winsize', 'windowsize', 'fftsize', 'window'):
        try:
            getattr(spectrum.par, _wp).val = 512
            break
        except AttributeError:
            continue
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 500
    connect_op(spec_data, 0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Phong material ────────────────────────────────────────────────────────

    mat = create_op(p, 'phong_mat', 'phongMAT')
    mat.nodeX, mat.nodeY = -300, 300
    mat.par.emitcolorr.expr = f"0.1 + ({MID})  * 0.9"
    mat.par.emitcolorg.expr = f"0.3 + ({HIGH}) * 0.7"
    mat.par.emitcolorb.expr = f"1.0 - ({BASS}) * 0.7"

    # ── Geo COMP + SOP network ────────────────────────────────────────────────

    geo = create_op(p, 'particle_geo', 'geoComp', 'geoCOMP')
    geo.nodeX, geo.nodeY = 0, 500

    grid = create_op(geo, 'grid_source', 'gridSOP')
    grid.nodeX, grid.nodeY = -300, 0
    grid.par.rows = 5
    grid.par.cols = 5

    particles = create_op(geo, 'particles', 'particleSOP')
    particles.nodeX, particles.nodeY = -100, 0
    connect_op(particles, 0, grid)
    particles.par.birthrate.expr   = f"10 + ({BASS}) * 800"
    particles.par.lifespanmax.expr = f"3.0 - ({MID}) * 2.0"
    particles.par.lifespanmin      = 0.3

    # Y-velocity and turbulence parameter names vary by TD version
    for vel_par in ('vy', 'vely', 'velocitiesy'):
        try:
            getattr(particles.par, vel_par).expr = f"0.3 + ({MID}) * 2.5"
            break
        except AttributeError:
            continue
    else:
        print("  Note: Y-velocity param not found — set it manually on 'particles'")

    for turb_par in ('turbulencer', 'turb', 'turbulence'):
        try:
            getattr(particles.par, turb_par).expr = f"0.05 + ({HIGH}) * 3.0"
            break
        except AttributeError:
            continue
    else:
        print("  Note: turbulence param not found — set it manually on 'particles'")

    sop_out = create_op(geo, 'geo_out', 'nullSOP')
    sop_out.nodeX, sop_out.nodeY = 100, 0
    connect_op(sop_out, 0, particles)
    sop_out.par.displayflag = True
    sop_out.par.renderflag  = True

    # ── Camera + Light ────────────────────────────────────────────────────────

    cam = create_op(p, 'camera', 'cameraComp', 'cameraCOMP')
    cam.nodeX, cam.nodeY = 0, 300
    cam.par.tz  = 5.0
    cam.par.fov = 50.0

    light = create_op(p, 'light1', 'lightComp', 'lightCOMP')
    light.nodeX, light.nodeY = 200, 300
    light.par.tx = 2.0
    light.par.ty = 4.0
    light.par.tz = 3.0

    # ── Render TOP ────────────────────────────────────────────────────────────

    render = create_op(p, 'render_scene', 'renderTOP')
    render.nodeX, render.nodeY = 200, 500
    render.par.camera = cam.path
    render.par.lights  = light.path
    render.par.bgcolorr = 0.01
    render.par.bgcolorg = 0.01
    render.par.bgcolorb = 0.03

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = create_op(p, 'glow', 'glowTOP')
    glow.nodeX, glow.nodeY = 400, 500
    glow.par.size.expr     = f"3 + ({BASS}) * 35"
    glow.par.strength.expr = f"0.3 + ({MID}) * 2.0"
    connect_op(glow, 0, render)

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = 400, 300

    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = 600, 300
    fade.par.brightness.expr = f"0.80 + ({BASS}) * 0.16"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 600, 500
    comp_fb.par.operand = 'add'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, glow)
    feedback.par.top = comp_fb.name

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 800, 500
    connect_op(output, 0, comp_fb)

    print("=" * 55)
    print("Network 04: 3D Particle System — BUILT in", p.path)
    print()
    print("REQUIRED: Select 'particle_geo' → Parameters → Render tab")
    print(f"          Set Material to: {mat.path}")
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Black render: check render_scene Camera/Lights, move camera back")
    print("=" * 55)


build()
