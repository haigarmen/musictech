"""
Network 02: Spectrum Bars
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.
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
        f"Cannot create '{type_name}'. Add it manually (right-click → Add Operator"
        f", search '{short}', rename to '{node_name}'). Run diagnose.py for help."
    )


def build():
    p = me.parent()

    # ── Audio → Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audiodevInCHOP', 'audio_in')
    audio.nodeX, audio.nodeY = -900, 100

    # Spectrum CHOP: FFT → 512 frequency-bin channels
    spectrum = create_op(p, 'spectrumCHOP', 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -700, 100
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = create_op(p, 'nullCHOP', 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -500, 100
    spec_data.setInput(0, spectrum)

    # ── CHOP to TOP: channels → pixels ────────────────────────────────────────

    chop_top = create_op(p, 'choptoTOP', 'chop_to_top')
    chop_top.nodeX, chop_top.nodeY = -300, 100
    chop_top.setInput(0, spec_data)

    # Rotate 90° so frequency bins run left→right as vertical bars
    transform = create_op(p, 'transformTOP', 'bars_transform')
    transform.nodeX, transform.nodeY = -100, 100
    transform.par.rz = 90
    transform.par.sy = 12.0
    transform.setInput(0, chop_top)

    # Spectrum values are tiny — amplify hard. Raise to 50–200 if bars invisible.
    level = create_op(p, 'levelTOP', 'level_amplify')
    level.nodeX, level.nodeY = 100, 100
    level.par.brightness = 30.0
    level.par.gamma      = 0.6
    level.setInput(0, transform)

    # ── Colour ────────────────────────────────────────────────────────────────

    ramp = create_op(p, 'rampTOP', 'ramp_color')
    ramp.nodeX, ramp.nodeY = 100, -100
    ramp.par.type = 'horizontal'
    # After building: select ramp_color and add colour stops in Parameters
    # (e.g. black at 0, blue at 0.3, cyan at 0.7, white at 1.0)

    color_mult = create_op(p, 'compositeTOP', 'color_multiply')
    color_mult.nodeX, color_mult.nodeY = 300, 100
    color_mult.par.operand = 'multiply'
    color_mult.setInput(0, level)
    color_mult.setInput(1, ramp)

    # ── Energy-driven glow ────────────────────────────────────────────────────

    energy = create_op(p, 'analyzeCHOP', 'analyze_energy')
    energy.nodeX, energy.nodeY = -700, -100
    energy.par.function = 'rms'
    energy.setInput(0, audio)

    e_gain = create_op(p, 'mathCHOP', 'energy_gain')
    e_gain.nodeX, e_gain.nodeY = -500, -100
    e_gain.par.gain = 5.0
    e_gain.setInput(0, energy)

    e_data = create_op(p, 'nullCHOP', 'energy_data')
    e_data.nodeX, e_data.nodeY = -300, -100
    e_data.setInput(0, e_gain)

    glow = create_op(p, 'glowTOP', 'glow')
    glow.nodeX, glow.nodeY = 500, 100
    glow.par.size.expr     = "3 + op('energy_data')[0] * 20"
    glow.par.strength.expr = "0.2 + op('energy_data')[0] * 1.5"
    glow.setInput(0, color_mult)

    output = create_op(p, 'nullTOP', 'OUTPUT')
    output.nodeX, output.nodeY = 700, 100
    output.setInput(0, glow)

    print("=" * 55)
    print("Network 02: Spectrum Bars — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ Bars invisible: select level_amplify, raise Brightness (50–200)")
    print("→ Customize colours: select ramp_color, add colour stops")
    print("=" * 55)


build()
