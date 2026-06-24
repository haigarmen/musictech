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
    audio.nodeX, audio.nodeY = -900, 500

    spectrum = create_op(p, 'spectrumCHOP', 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 500
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = create_op(p, 'nullCHOP', 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 500
    spec_data.setInput(0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Phong material ────────────────────────────────────────────────────────

    mat = create_op(p, 'phongMAT', 'phong_mat')
    mat.nodeX, mat.nodeY = -300, 300
    mat.par.emitcolorr.expr = f"0.1 + ({MID})  * 0.9"
    mat.par.emitcolorg.expr = f"0.3 + ({HIGH}) * 0.7"
    mat.par.emitcolorb.expr = f"1.0 - ({BASS}) * 0.7"

    # ── Geo COMP + SOP network ────────────────────────────────────────────────

    geo = create_op(p, 'geoComp', 'particle_geo')
    geo.nodeX, geo.nodeY = 0, 500

    grid = create_op(geo, 'gridSOP', 'grid_source')
    grid.nodeX, grid.nodeY = -300, 0
    grid.par.rows = 5
    grid.par.cols = 5

    particles = create_op(geo, 'particleSOP', 'particles')
    particles.nodeX, particles.nodeY = -100, 0
    particles.setInput(0, grid)
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

    sop_out = create_op(geo, 'nullSOP', 'geo_out')
    sop_out.nodeX, sop_out.nodeY = 100, 0
    sop_out.setInput(0, particles)
    sop_out.par.displayflag = True
    sop_out.par.renderflag  = True

    # ── Camera + Light ────────────────────────────────────────────────────────

    cam = create_op(p, 'cameraComp', 'camera')
    cam.nodeX, cam.nodeY = 0, 300
    cam.par.tz  = 5.0
    cam.par.fov = 50.0

    light = create_op(p, 'lightComp', 'light1')
    light.nodeX, light.nodeY = 200, 300
    light.par.tx = 2.0
    light.par.ty = 4.0
    light.par.tz = 3.0

    # ── Render TOP ────────────────────────────────────────────────────────────

    render = create_op(p, 'renderTOP', 'render_scene')
    render.nodeX, render.nodeY = 200, 500
    render.par.camera = cam.path
    render.par.lights  = light.path
    render.par.bgcolorr = 0.01
    render.par.bgcolorg = 0.01
    render.par.bgcolorb = 0.03

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = create_op(p, 'glowTOP', 'glow')
    glow.nodeX, glow.nodeY = 400, 500
    glow.par.size.expr     = f"3 + ({BASS}) * 35"
    glow.par.strength.expr = f"0.3 + ({MID}) * 2.0"
    glow.setInput(0, render)

    feedback = create_op(p, 'feedbackTOP', 'feedback')
    feedback.nodeX, feedback.nodeY = 400, 300

    fade = create_op(p, 'levelTOP', 'feedback_fade')
    fade.nodeX, fade.nodeY = 600, 300
    fade.par.brightness.expr = f"0.80 + ({BASS}) * 0.16"
    fade.setInput(0, feedback)

    comp_fb = create_op(p, 'compositeTOP', 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 600, 500
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, glow)
    feedback.par.top = comp_fb.name

    output = create_op(p, 'nullTOP', 'OUTPUT')
    output.nodeX, output.nodeY = 800, 500
    output.setInput(0, comp_fb)

    print("=" * 55)
    print("Network 04: 3D Particle System — BUILT in", p.path)
    print()
    print("REQUIRED: Select 'particle_geo' → Parameters → Render tab")
    print(f"          Set Material to: {mat.path}")
    print()
    print("→ Right-click OUTPUT → View")
    print("→ Black render: check render_scene Camera/Lights, move camera back")
    print("=" * 55)


build()
