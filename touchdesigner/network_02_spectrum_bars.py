"""
Network 02: Spectrum Bars
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
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

    # ── Audio → Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP')
    audio.nodeX, audio.nodeY = -900, 100

    spectrum = create_op(p, 'spectrum', 'audiospectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 100
    spectrum.par.fftsize = 512
    connect_op(spectrum, 0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 100
    connect_op(spec_data, 0, spectrum)

    # ── CHOP to TOP ───────────────────────────────────────────────────────────
    # choptoTOP has no wired inputs — connect_op sets par.chop automatically.

    chop_top = create_op(p, 'chop_to_top', 'choptoTOP')
    chop_top.nodeX, chop_top.nodeY = -300, 100
    connect_op(chop_top, 0, spec_data)

    # Rotate 90° so frequency bins run left→right as vertical bars
    transform = create_op(p, 'bars_transform', 'transformTOP')
    transform.nodeX, transform.nodeY = -100, 100
    transform.par.rotate = 90
    transform.par.sy = 12.0
    connect_op(transform, 0, chop_top)

    # Amplify — spectrum values are very small. Raise brightness if bars invisible.
    level = create_op(p, 'level_amplify', 'levelTOP')
    level.nodeX, level.nodeY = 100, 100
    level.par.brightness1 = 30.0
    level.par.gamma1      = 0.6
    connect_op(level, 0, transform)

    # ── Colour ramp ───────────────────────────────────────────────────────────

    ramp = create_op(p, 'ramp_color', 'rampTOP')
    ramp.nodeX, ramp.nodeY = 100, -100
    ramp.par.type = 'horizontal'

    color_mult = create_op(p, 'color_multiply', 'compositeTOP')
    color_mult.nodeX, color_mult.nodeY = 300, 100
    color_mult.par.operand = 'multiply'
    connect_op(color_mult, 0, level)
    connect_op(color_mult, 1, ramp)

    # ── Energy glow ───────────────────────────────────────────────────────────

    energy = create_op(p, 'analyze_energy', 'analyzeCHOP')
    energy.nodeX, energy.nodeY = -700, -100
    energy.par.function = 'rms'
    connect_op(energy, 0, audio)

    e_gain = create_op(p, 'energy_gain', 'mathCHOP')
    e_gain.nodeX, e_gain.nodeY = -500, -100
    e_gain.par.gain = 5.0
    connect_op(e_gain, 0, energy)

    e_data = create_op(p, 'energy_data', 'nullCHOP')
    e_data.nodeX, e_data.nodeY = -300, -100
    connect_op(e_data, 0, e_gain)

    prev_top = color_mult

    glow = try_create(p, 'glow', 'glowTOP', 'bloomTOP')
    if glow is not None:
        glow.nodeX, glow.nodeY = 500, 100
        try:
            glow.par.size.expr     = "3 + op('energy_data')[0] * 20"
            glow.par.strength.expr = "0.2 + op('energy_data')[0] * 1.5"
        except AttributeError:
            pass
        connect_op(glow, 0, color_mult)
        prev_top = glow

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 700, 100
    connect_op(output, 0, prev_top)

    print("=" * 55)
    print("Network 02: Spectrum Bars — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Bars invisible: select level_amplify, raise Brightness1 (50–200)")
    print("→ Customize colours: select ramp_color, add colour stops")
    print("=" * 55)


build()
