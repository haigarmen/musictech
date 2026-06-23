"""
Network 04: 3D Audio-Reactive Particle System
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.

WHAT GETS BUILT:
  Audio In → Spectrum → spectrum_data (Null CHOP)

  Inside a Geo COMP:
    Grid SOP (birth positions) → Particle SOP (simulated particles) → Null SOP

  Scene: Geo COMP + Camera COMP + Light COMP → Render TOP
  Post: Glow TOP + Feedback trail → Null TOP (OUTPUT)

THREE-BAND CONTROL:
  Bass  → particle birth rate  (kick drum = burst of new particles)
  Mid   → upward velocity      (melody = particles float higher / faster)
  High  → turbulence           (hi-hats = particles scatter and jitter)

AFTER BUILDING — IMPORTANT MANUAL STEPS:
  1. Select the Geo COMP ('particle_geo'). In its parameters, go to the Render tab
     and set 'Material' to the Phong MAT that was created ('phong_mat').
  2. If particles aren't visible: select 'render_scene', check that Camera and Lights
     point to the correct COMPs.
  3. The Particle SOP inside the Geo COMP — double-click the Geo COMP to go inside,
     then select 'particles' and adjust Birth Rate if nothing appears.

TROUBLESHOOTING:
  • Black render: check render_scene has camera='camera' and lights='light1'.
  • No particles: inside particle_geo, select 'particles' → increase Birth Rate.
  • Particles off-screen: select 'camera' COMP and move it further back (tz = 5+).
"""


def build():
    p = me.parent()

    # ── Audio + spectrum ──────────────────────────────────────────────────────

    audio = p.create(audiodevInCHOP, 'audio_in')
    audio.nodeX, audio.nodeY = -900, 400

    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 400
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = p.create(nullCHOP, 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 400
    spec_data.setInput(0, spectrum)

    # Band expressions — same pattern as Network 03
    BASS  = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4]) * 60, 0, 1)"
    MID   = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35]) * 90, 0, 1)"
    HIGH  = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120]) * 120, 0, 1)"

    # ── Phong material ────────────────────────────────────────────────────────
    # Emissive color makes particles glow even without a nearby light.
    mat = p.create(phongMAT, 'phong_mat')
    mat.nodeX, mat.nodeY = -300, 200
    mat.par.emitcolorr.expr = f"0.1 + ({MID})  * 0.9"
    mat.par.emitcolorg.expr = f"0.3 + ({HIGH}) * 0.7"
    mat.par.emitcolorb.expr = f"1.0 - ({BASS}) * 0.7"

    # ── Geo COMP: contains all 3D geometry SOPs ───────────────────────────────
    geo = p.create(geoComp, 'particle_geo')
    geo.nodeX, geo.nodeY = 0, 400

    # After building, manually assign phong_mat in Geo's Render → Material param.
    # Script note: geo.par.mat references vary by TD version; set it in the UI.

    # ── SOP network inside the Geo COMP ──────────────────────────────────────
    # Go inside particle_geo to create the SOP operators.

    grid = geo.create(gridSOP, 'grid_source')
    grid.nodeX, grid.nodeY = -300, 0
    grid.par.rows = 5
    grid.par.cols = 5   # 25 birth-position points on a 5×5 grid

    # Particle SOP: simulation node.
    # Each frame births new particles from the grid, moves them, then ages them out.
    particles = geo.create(particleSOP, 'particles')
    particles.nodeX, particles.nodeY = -100, 0
    particles.setInput(0, grid)

    # Birth rate: baseline 10/sec + up to 800 extra on a hard bass hit.
    # The expression references the CHOP in the PARENT container (p, not geo).
    particles.par.birthrate.expr   = f"10 + ({BASS}) * 800"
    # Lifespan: particles live 0.5–3 seconds (shorter when energy is high = fast turnover)
    particles.par.lifespanmax.expr = f"3.0 - ({MID}) * 2.0"
    particles.par.lifespanmin      = 0.3

    # Upward launch velocity: mid band makes particles fly higher
    # Note: if 'vy' throws an error in your TD version, set it manually on the Particle SOP
    try:
        particles.par.vy.expr = f"0.3 + ({MID}) * 2.5"
    except AttributeError:
        print("  Note: vy parameter not found — set initial Y velocity manually on 'particles'")

    # Turbulence: high freq = scatter/jitter
    try:
        particles.par.turbulencer.expr = f"0.05 + ({HIGH}) * 3.0"
    except AttributeError:
        print("  Note: turbulencer not found — set turbulence manually on 'particles'")

    # Output SOP: marks what the Geo COMP renders
    sop_out = geo.create(nullSOP, 'geo_out')
    sop_out.nodeX, sop_out.nodeY = 100, 0
    sop_out.setInput(0, particles)
    sop_out.par.displayflag = True
    sop_out.par.renderflag  = True

    # ── Camera and Light ──────────────────────────────────────────────────────

    cam = p.create(cameraComp, 'camera')
    cam.nodeX, cam.nodeY = 0, 200
    cam.par.tz = 5.0    # move camera back so scene is in view
    cam.par.fov = 50.0

    light = p.create(lightComp, 'light1')
    light.nodeX, light.nodeY = 200, 200
    light.par.tx =  2.0
    light.par.ty =  4.0
    light.par.tz =  3.0

    # ── Render TOP: combines geo + camera + light into a 2D image ─────────────

    render = p.create(renderTOP, 'render_scene')
    render.nodeX, render.nodeY = 200, 400
    render.par.camera = cam.path
    render.par.lights  = light.path
    # Black background so particles are clearly visible
    render.par.bgcolorr = 0.01
    render.par.bgcolorg = 0.01
    render.par.bgcolorb = 0.03

    # ── Post-processing ───────────────────────────────────────────────────────

    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 400, 400
    glow.par.size.expr     = f"3 + ({BASS}) * 35"
    glow.par.strength.expr = f"0.3 + ({MID}) * 2.0"
    glow.setInput(0, render)

    # Feedback trail (same pattern as Network 03)
    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = 400, 200

    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = 600, 200
    fade.par.brightness.expr = f"0.80 + ({BASS}) * 0.16"
    fade.setInput(0, feedback)

    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 600, 400
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, glow)

    feedback.par.top = comp_fb.name

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 800, 400
    output.setInput(0, comp_fb)

    print("=" * 50)
    print("Network 04: 3D Particle System — BUILT")
    print("Container:", p.path)
    print()
    print("REQUIRED MANUAL STEP:")
    print("  Select 'particle_geo' → Parameters → Render tab")
    print("  Set 'Material' to:", mat.path)
    print()
    print("If render is black:")
    print("  Select 'render_scene' → check Camera and Lights paths")
    print("  Move 'camera' further back: set tz = 8 or 10")
    print()
    print("Right-click OUTPUT → View")
    print("=" * 50)


build()
