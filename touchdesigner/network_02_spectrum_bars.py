"""
Network 02: Spectrum Bars
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Paste into a Text DAT inside a Base COMP, set Language = Python, Run Script.
  If you get a NameError, run diagnose.py first.

WHAT GETS BUILT:
  Audio Device In → Spectrum CHOP → CHOP to TOP → Transform → Level → Composite
  Ramp (colour) ──────────────────────────────────────────────────↗
  Energy glow drives a Glow TOP → Null TOP (OUTPUT)
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


def build():
    p = me.parent()

    # ── Audio → Spectrum ──────────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP', 'audiodevInCHOP')
    audio.nodeX, audio.nodeY = -900, 100

    # Spectrum CHOP: FFT → 512 frequency-bin channels
    spectrum = create_op(p, 'spectrum', 'spectrumCHOP', 'audiospectrumCHOP')
    spectrum.nodeX, spectrum.nodeY = -700, 100
    for _wp in ('windowsize', 'winsize', 'fftsize', 'window'):
        try:
            getattr(spectrum.par, _wp).val = 512
            break
        except AttributeError:
            continue
    spectrum.setInput(0, audio)

    spec_data = create_op(p, 'spectrum_data', 'nullCHOP')
    spec_data.nodeX, spec_data.nodeY = -500, 100
    spec_data.setInput(0, spectrum)

    # ── CHOP to TOP: channels → pixels ────────────────────────────────────────

    chop_top = create_op(p, 'chop_to_top', 'choptoTOP')
    chop_top.nodeX, chop_top.nodeY = -300, 100
    chop_top.setInput(0, spec_data)

    # Rotate 90° so frequency bins run left→right as vertical bars
    transform = create_op(p, 'bars_transform', 'transformTOP')
    transform.nodeX, transform.nodeY = -100, 100
    transform.par.rz = 90
    transform.par.sy = 12.0
    transform.setInput(0, chop_top)

    # Spectrum values are tiny — amplify hard. Raise to 50–200 if bars invisible.
    level = create_op(p, 'level_amplify', 'levelTOP')
    level.nodeX, level.nodeY = 100, 100
    level.par.brightness = 30.0
    level.par.gamma      = 0.6
    level.setInput(0, transform)

    # ── Colour ────────────────────────────────────────────────────────────────

    ramp = create_op(p, 'ramp_color', 'rampTOP')
    ramp.nodeX, ramp.nodeY = 100, -100
    ramp.par.type = 'horizontal'
    # After building: select ramp_color and add colour stops in Parameters
    # (e.g. black at 0, blue at 0.3, cyan at 0.7, white at 1.0)

    color_mult = create_op(p, 'color_multiply', 'compositeTOP')
    color_mult.nodeX, color_mult.nodeY = 300, 100
    color_mult.par.operand = 'multiply'
    color_mult.setInput(0, level)
    color_mult.setInput(1, ramp)

    # ── Energy-driven glow ────────────────────────────────────────────────────

    energy = create_op(p, 'analyze_energy', 'analyzeCHOP')
    energy.nodeX, energy.nodeY = -700, -100
    energy.par.function = 'rms'
    energy.setInput(0, audio)

    e_gain = create_op(p, 'energy_gain', 'mathCHOP')
    e_gain.nodeX, e_gain.nodeY = -500, -100
    e_gain.par.gain = 5.0
    e_gain.setInput(0, energy)

    e_data = create_op(p, 'energy_data', 'nullCHOP')
    e_data.nodeX, e_data.nodeY = -300, -100
    e_data.setInput(0, e_gain)

    glow = create_op(p, 'glow', 'glowTOP')
    glow.nodeX, glow.nodeY = 500, 100
    glow.par.size.expr     = "3 + op('energy_data')[0] * 20"
    glow.par.strength.expr = "0.2 + op('energy_data')[0] * 1.5"
    glow.setInput(0, color_mult)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = 700, 100
    output.setInput(0, glow)

    print("=" * 55)
    print("Network 02: Spectrum Bars — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Bars invisible: select level_amplify, raise Brightness (50–200)")
    print("→ Customize colours: select ramp_color, add colour stops")
    print("=" * 55)


build()
