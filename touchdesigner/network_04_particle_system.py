"""
Network 04: Audio-Reactive 3D Particle System
===============================================
A full 3D rendering pipeline where bass drives particle birth rate,
mid frequencies drive particle speed, and high frequencies add turbulence.
Particles are rendered with a Phong material and post-processed with glow
and a feedback trail, building on every technique from Networks 01–03.

Signal Flow:
    [Audio In] ──→ bass / mid / high band analysis (same as Network 03)
                                │
    [Grid SOP] → [Particle SOP] (expressions on birth, speed, turbulence)
                       │
              [Null SOP] → [Geo COMP] + [Camera COMP] + [Light COMP]
                                  │
                            [Render TOP]
                                  │
                     [Glow TOP] → [Feedback trail] → [Null TOP: OUTPUT]

Concepts introduced:
    - Full 3D pipeline: SOP → Geo COMP → Camera/Light → Render TOP
    - Particle SOP: birth rate, life, gravity, turbulence, drag
    - Phong MAT: basic lit material with audio-reactive emissive color
    - Render TOP: renders the 3D scene to a 2D image
    - Post-processing stack on top of 3D render

How to run:
    Paste into a Text DAT inside a Base COMP and Run Script.
    The script builds everything in BUILD_PATH.
"""

BUILD_PATH = '/project1'


def build():
    p = op(BUILD_PATH)
    if p is None:
        print(f"ERROR: '{BUILD_PATH}' not found.")
        return

    # ── Audio analysis (3 bands) ──────────────────────────────────────────────
    # Identical band-extraction pattern to Network 03.

    audio_in = p.create(audiodevInCHOP, 'audio_in')
    audio_in.nodeX, audio_in.nodeY = -1400, 600
    audio_in.par.rate = 44100

    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -1200, 600
    spectrum.par.windowsize = 512
    spectrum.par.overlap    = 0.75
    spectrum.setInput(0, audio_in)

    band_defs = [
        ('bass',  0,   10, -1000, 800),
        ('mid',   10,  60, -1000, 600),
        ('high',  60, 200, -1000, 400),
    ]
    nulls = {}
    for name, ch_start, ch_end, nx, ny in band_defs:
        sel = p.create(selectCHOP, f'select_{name}')
        sel.nodeX, sel.nodeY = nx, ny
        sel.par.chanstart = ch_start
        sel.par.chanend   = ch_end - 1
        sel.setInput(0, spectrum)

        analyze = p.create(analyzeCHOP, f'analyze_{name}')
        analyze.nodeX, analyze.nodeY = nx + 200, ny
        analyze.par.function = 'average'
        analyze.setInput(0, sel)

        filt = p.create(filterCHOP, f'filter_{name}')
        filt.nodeX, filt.nodeY = nx + 400, ny
        filt.par.width = 0.04
        filt.setInput(0, analyze)

        math = p.create(mathCHOP, f'math_{name}')
        math.nodeX, math.nodeY = nx + 600, ny
        math.par.gain  = 14.0
        math.par.clamp = True
        math.par.clampmin = 0.0
        math.par.clampmax = 1.0
        math.setInput(0, filt)

        null = p.create(nullCHOP, f'data_{name}')
        null.nodeX, null.nodeY = nx + 800, ny
        null.setInput(0, math)
        nulls[name] = null

    # ── Particle material ─────────────────────────────────────────────────────

    mat = p.create(phongMAT, 'particle_mat')
    mat.nodeX, mat.nodeY = -400, 800
    # Emissive color shifts with mid frequencies (makes particles glow)
    mat.par.emitcolorr.expr = "0.2 + op('data_mid')['chan1']  * 0.8"
    mat.par.emitcolorg.expr = "0.5 + op('data_high')['chan1'] * 0.5"
    mat.par.emitcolorb.expr = "1.0 - op('data_bass')['chan1'] * 0.6"
    mat.par.ambientcolorr = 0.0
    mat.par.ambientcolorg = 0.0
    mat.par.ambientcolorb = 0.0
    mat.par.shininess = 60

    # ── 3D scene components ───────────────────────────────────────────────────

    # Geo COMP: container for all geometry operators
    geo = p.create(geoComp, 'particle_geo')
    geo.nodeX, geo.nodeY = 0, 600
    geo.par.matx = mat.path   # apply the Phong material

    # Camera: looking down -Z axis with some perspective
    cam = p.create(cameraComp, 'camera')
    cam.nodeX, cam.nodeY = 0, 400
    cam.par.tz = 5.0
    cam.par.fov = 45.0

    # Point light above the scene
    light = p.create(lightComp, 'light')
    light.nodeX, light.nodeY = 0, 200
    light.par.tx =  2.0
    light.par.ty =  3.0
    light.par.tz =  4.0

    # ── Geometry inside the Geo COMP ──────────────────────────────────────────
    # TouchDesigner requires SOPs to live inside a Geo COMP.
    # We navigate inside it to create the SOP network.

    # Point grid: defines where particles are born
    grid = geo.create(gridSOP, 'grid_source')
    grid.nodeX, grid.nodeY = -400, 0
    grid.par.rows = 4
    grid.par.cols = 4
    grid.par.ty   = 0.0

    # Particle SOP: the simulation
    # bass  → birthrate  (more particles on kick/bass hits)
    # mid   → speed (vy) (particles fly faster on melodic energy)
    # high  → turbulence (chaotic shimmer on hi-hats / transients)
    particles = geo.create(particleSOP, 'particles')
    particles.nodeX, particles.nodeY = -200, 0
    particles.setInput(0, grid)           # source positions
    # Birth rate: 20 base + up to 500 extra on hard bass hits
    particles.par.birthrate.expr   = "20 + op('data_bass')['chan1'] * 500"
    # Lifespan: longer at rest, shorter when energy is high (more turnover)
    particles.par.lifespanmax.expr = "3.0 - op('data_mid')['chan1']  * 2.0"
    particles.par.lifespanmin.expr = "0.5"
    # Upward velocity driven by mid band
    particles.par.vy.expr          = "0.5 + op('data_mid')['chan1']  * 2.5"
    # Turbulence: high frequencies cause random scattering
    particles.par.turbulencer.expr = "0.1 + op('data_high')['chan1'] * 3.0"
    # Light drag so particles float rather than rocket
    particles.par.dragr            = 0.08

    # Null SOP inside Geo: the final geometry output
    sop_out = geo.create(nullSOP, 'geo_out')
    sop_out.nodeX, sop_out.nodeY = 0, 0
    sop_out.setInput(0, particles)
    sop_out.par.displayflag = True
    sop_out.par.renderflag  = True

    # ── Render TOP ────────────────────────────────────────────────────────────

    render = p.create(renderTOP, 'render_scene')
    render.nodeX, render.nodeY = 200, 600
    render.par.camera  = cam.path
    render.par.lights  = light.path
    render.par.bgcolorr = 0.01
    render.par.bgcolorg = 0.01
    render.par.bgcolorb = 0.03

    # ── Post-processing ───────────────────────────────────────────────────────

    # Glow: particles bloom on loud moments
    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 400, 600
    glow.par.size.expr     = "4 + op('data_bass')['chan1'] * 30"
    glow.par.strength.expr = "0.5 + op('data_mid')['chan1'] * 2.0"
    glow.setInput(0, render)

    # Feedback trail (same pattern as Network 03)
    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = 400, 400

    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = 600, 400
    fade.par.brightness.expr = "0.85 + op('data_bass')['chan1'] * 0.12"
    fade.setInput(0, feedback)

    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 600, 600
    comp_fb.par.operand = 'add'
    comp_fb.setInput(0, fade)
    comp_fb.setInput(1, glow)

    feedback.par.top = comp_fb.name

    # Final output
    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 800, 600
    output.setInput(0, comp_fb)

    print("✓  Network 04 built.")
    print("   3D particles burst on bass, scatter on highs, flow on mids.")
    print("   TIP: Select 'camera' COMP and adjust tz/fov to frame the scene.")
    print("   TIP: Select 'particle_mat' and tweak emissive color expressions.")

build()
