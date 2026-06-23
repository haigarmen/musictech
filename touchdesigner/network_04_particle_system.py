"""
Network 04: 3D Audio-Reactive Particle System
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

WHAT GETS BUILT:
  Audio In → Spectrum → spectrum_data CHOP
  Phong MAT (emissive colour driven by audio)
  Geo COMP containing: Grid SOP → Particle SOP → Null SOP
  Camera COMP + Light COMP + Render TOP
  Glow TOP + Feedback trail → Null TOP (OUTPUT)

AFTER BUILDING — REQUIRED MANUAL STEP:
  Select 'particle_geo' → open Parameters → Render tab
  Set 'Material' to the path of 'phong_mat' (e.g. ../phong_mat)
  Without this the particles will render without colour/glow.

THREE-BAND CONTROL:
  Bass  → birth rate (kick = burst of new particles)
  Mid   → upward velocity + emissive colour
  High  → turbulence / scattering
"""


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
    print(f"Run in Textport: [x for x in dir() if x.endswith('CHOP')]")
    print(f"Sample CHOPs: {chops[:6]}  Sample TOPs: {tops[:6]}")
    raise NameError(f"TD types not found: {names}")


def build():
    p = me.parent()

    # ── Audio + Spectrum ──────────────────────────────────────────────────────

    audio = p.create(td_op('audiodevInCHOP'), 'audio_in')
    audio.nodeX, audio.nodeY = -900, 500

    spectrum = p.create(td_op('spectrumCHOP'), 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 500
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = p.create(td_op('nullCHOP'), 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 500
    spec_data.setInput(0, spectrum)

    BASS = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60, 0, 1)"
    MID  = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90, 0, 1)"
    HIGH = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120, 0, 1)"

    # ── Phong material ────────────────────────────────────────────────────────

    mat = p.create(td_op('phongMAT'), 'phong_mat')
    mat.nodeX, mat.nodeY = -300, 300
    mat.par.emitcolorr.expr = f"0.1 + ({MID})  * 0.9"
    mat.par.emitcolorg.expr = f"0.3 + ({HIGH}) * 0.7"
    mat.par.emitcolorb.expr = f"1.0 - ({BASS}) * 0.7"

    # ── Geo COMP (contains all geometry SOPs) ────────────────────────────────

    geo = p.create(td_op('geoComp'), 'particle_geo')
    geo.nodeX, geo.nodeY = 0, 500

    # Go inside the Geo COMP to create SOPs
    grid = geo.create(td_op('gridSOP'), 'grid_source')
    grid.nodeX, grid.nodeY = -300, 0
    grid.par.rows = 5
    grid.par.cols = 5    # 25 birth positions on a flat 5×5 grid

    particles = geo.create(td_op('particleSOP'), 'particles')
    particles.nodeX, particles.nodeY = -100, 0
    particles.setInput(0, grid)
    # Birth rate: low baseline, surges on hard bass hits
    particles.par.birthrate.expr   = f"10 + ({BASS}) * 800"
    # Lifespan shortens when energy is high (faster turnover = denser look)
    particles.par.lifespanmax.expr = f"3.0 - ({MID}) * 2.0"
    particles.par.lifespanmin      = 0.3

    # Initial upward velocity — mid band makes particles fly higher
    # 'vy' name may differ by TD version; wrapped in try/except
    for vel_par in ('vy', 'vely', 'velocitiesy'):
        try:
            getattr(particles.par, vel_par).expr = f"0.3 + ({MID}) * 2.5"
            break
        except AttributeError:
            continue
    else:
        print("  Note: couldn't find Y-velocity param — set it manually on 'particles'")

    # Turbulence — high frequencies cause random scattering
    for turb_par in ('turbulencer', 'turb', 'turbulence'):
        try:
            getattr(particles.par, turb_par).expr = f"0.05 + ({HIGH}) * 3.0"
            break
        except AttributeError:
            continue
    else:
        print("  Note: couldn't find turbulence param — set it manually on 'particles'")

    sop_out = geo.create(td_op('nullSOP'), 'geo_out')
    sop_out.nodeX, sop_out.nodeY = 100, 0
    sop_out.setInput(0, particles)
    sop_out.par.displayflag = True
    sop_out.par.renderflag  = True

    # ── Camera + Light ────────────────────────────────────────────────────────

    cam = p.create(td_op('cameraComp'), 'camera')
    cam.nodeX, cam.nodeY = 0, 300
    cam.par.tz  = 5.0
    cam.par.fov = 50.0

    light = p.create(td_op('lightComp'), 'light1')
    light.nodeX, light.nodeY = 200, 300
    light.par.tx = 2.0
    light.par.ty = 4.0
    light.par.tz = 3.0

    # ── Render TOP ────────────────────────────────────────────────────────────

    render = p.create(td_op('renderTOP'), 'render_scene')
    render.nodeX, render.nodeY = 200, 500
    render.par.camera = cam.path
    render.par.lights  = light.path
    render.par.bgcolorr = 0.01
    render.par.bgcolorg = 0.01
    render.par.bgcolorb = 0.03

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = p.create(td_op('glowTOP'), 'glow')
    glow.nodeX, glow.nodeY = 400, 500
    glow.par.size.expr     = f"3 + ({BASS}) * 35"
    glow.par.strength.expr = f"0.3 + ({MID}) * 2.0"
    glow.setInput(0, render)

    feedback = p.create(td_op('feedbackTOP'), 'feedback')
    feedback.nodeX, feedback.nodeY = 400, 300

    fade = p.create(td_op('levelTOP'), 'feedback_fade')
    fade.nodeX, fade.nodeY = 600, 300
    fade.par.brightness.expr = f"0.80 + ({BASS}) * 0.16"
    fade.setInput(0, feedback)

    comp_fb = p.create(td_op('compositeTOP'), 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 600, 500
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, glow)
    feedback.par.top = comp_fb.name

    output = p.create(td_op('nullTOP'), 'OUTPUT')
    output.nodeX, output.nodeY = 800, 500
    output.setInput(0, comp_fb)

    print("=" * 55)
    print("Network 04: 3D Particle System — BUILT in", p.path)
    print()
    print("REQUIRED: Select 'particle_geo' → Parameters → Render tab")
    print(f"          Set 'Material' to:  {mat.path}")
    print()
    print("If render is black:")
    print("  Select render_scene → verify Camera and Lights paths")
    print("  Move 'camera' back: set tz = 8 or 10")
    print()
    print("→ Right-click OUTPUT → View")
    print("=" * 55)


build()
