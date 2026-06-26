"""
Network 04: 3D Audio-Reactive Particle System
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.

AFTER BUILDING — REQUIRED MANUAL STEP:
  Select 'particle_geo' → Parameters → Render tab → set Material to 'phong_mat'.

THREE-BAND CONTROL:
  Bass  → birth rate    Mid  → velocity + colour    High → turbulence

NOTE: If 'particle_geo' is skipped (geoComp unavailable via script), create it
manually: right-click → Add Operator → Geometry COMP, rename to 'particle_geo'.
Then re-run this script — it will populate the SOP network inside it.
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
    audio.nodeX, audio.nodeY = -900, 500

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 500
    spectrum.par.fftsize = 512
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 500
    connect_op(spec_data, 0, spectrum)

    BASS = "min(1.0, max(0.0, (op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4])*60))"
    MID  = "min(1.0, max(0.0, (op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35])*90))"
    HIGH = "min(1.0, max(0.0, (op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120])*120))"

    # ── Phong material ────────────────────────────────────────────────────────

    mat = try_create(p, 'phong_mat', 'phongMAT')
    if mat is not None:
        mat.nodeX, mat.nodeY = -300, 300
        try:
            mat.par.emitcolorr.expr = f"0.1 + ({MID})  * 0.9"
            mat.par.emitcolorg.expr = f"0.3 + ({HIGH}) * 0.7"
            mat.par.emitcolorb.expr = f"1.0 - ({BASS}) * 0.7"
        except AttributeError:
            pass

    # ── Geo COMP + SOP network ────────────────────────────────────────────────
    # geoComp may need to be created manually in some TD builds — see header note.

    geo = try_create(p, 'particle_geo', 'geoComp', 'geoCOMP')
    if geo is None:
        print()
        print("  ACTION NEEDED: Create Geometry COMP manually:")
        print("    right-click in network → Add Operator → Geometry COMP")
        print("    rename it to 'particle_geo', then re-run this script.")
        print()
        geo = op('particle_geo') if op('particle_geo') else None

    if geo is not None:
        geo.nodeX, geo.nodeY = 0, 500

        grid = try_create(geo, 'grid_source', 'gridSOP')
        if grid is not None:
            grid.nodeX, grid.nodeY = -300, 0
            grid.par.rows = 5
            grid.par.cols = 5

        particles = try_create(geo, 'particles', 'particleSOP')
        if particles is not None:
            particles.nodeX, particles.nodeY = -100, 0
            if grid is not None:
                connect_op(particles, 0, grid)
            try:
                particles.par.birthrate.expr   = f"10 + ({BASS}) * 800"
                particles.par.lifespanmax.expr = f"3.0 - ({MID}) * 2.0"
                particles.par.lifespanmin      = 0.3
            except AttributeError:
                pass
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

        sop_out = try_create(geo, 'geo_out', 'nullSOP')
        if sop_out is not None:
            sop_out.nodeX, sop_out.nodeY = 100, 0
            if particles is not None:
                connect_op(sop_out, 0, particles)
            try:
                sop_out.par.displayflag = True
                sop_out.par.renderflag  = True
            except AttributeError:
                pass

    # ── Camera + Light ────────────────────────────────────────────────────────

    cam = try_create(p, 'camera', 'cameraComp', 'cameraCOMP')
    if cam is not None:
        cam.nodeX, cam.nodeY = 0, 300
        try:
            cam.par.tz  = 5.0
            cam.par.fov = 50.0
        except AttributeError:
            pass
    else:
        print("  Note: Create Camera COMP manually, rename to 'camera'")

    light = try_create(p, 'light1', 'lightComp', 'lightCOMP')
    if light is not None:
        light.nodeX, light.nodeY = 200, 300
        try:
            light.par.tx = 2.0
            light.par.ty = 4.0
            light.par.tz = 3.0
        except AttributeError:
            pass
    else:
        print("  Note: Create Light COMP manually, rename to 'light1'")

    # ── Render TOP ────────────────────────────────────────────────────────────

    render = create_op(p, 'render_scene', 'renderTOP')
    render.nodeX, render.nodeY = 200, 500
    if cam is not None:
        try:
            render.par.camera = cam.path
        except AttributeError:
            pass
    if light is not None:
        try:
            render.par.lights = light.path
        except AttributeError:
            pass
    try:
        render.par.bgcolorr = 0.01
        render.par.bgcolorg = 0.01
        render.par.bgcolorb = 0.03
    except AttributeError:
        pass

    # ── Post-processing ───────────────────────────────────────────────────────

    prev_top = render

    glow = try_create(p, 'glow', 'glowTOP')
    if glow is not None:
        glow.nodeX, glow.nodeY = 400, 500
        try:
            glow.par.size.expr     = f"3 + ({BASS}) * 35"
            glow.par.strength.expr = f"0.3 + ({MID}) * 2.0"
        except AttributeError:
            pass
        connect_op(glow, 0, render)
        prev_top = glow

    feedback = create_op(p, 'feedback', 'feedbackTOP')
    feedback.nodeX, feedback.nodeY = 400, 300

    fade = create_op(p, 'feedback_fade', 'levelTOP')
    fade.nodeX, fade.nodeY = 600, 300
    fade.par.brightness1.expr = f"0.80 + ({BASS}) * 0.16"
    connect_op(fade, 0, feedback)

    comp_fb = create_op(p, 'comp_feedback', 'compositeTOP')
    comp_fb.nodeX, comp_fb.nodeY = 600, 500
    comp_fb.par.operand = 'add'
    connect_op(comp_fb, 0, fade)
    connect_op(comp_fb, 1, prev_top)
    feedback.par.top = comp_fb.name

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 800, 500
    connect_op(output, 0, comp_fb)

    print("=" * 55)
    print("Network 04: 3D Particle System — BUILT in", p.path)
    print()
    if mat is not None:
        print("REQUIRED: Select 'particle_geo' → Parameters → Render tab")
        print(f"          Set Material to: {mat.path}")
        print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Black render: check render_scene Camera/Lights, move camera back")
    print("=" * 55)


build()
