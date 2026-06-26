"""
Network 01: Basic Volume Pulse
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  1. In TouchDesigner, right-click in the network → Base
  2. Double-click the Base COMP to go inside it
  3. Right-click inside → DAT → Text
  4. Paste this entire script, set Language = Python, Run Script
  5. Right-click the OUTPUT node → View

WHAT GETS BUILT:
  Audio Device In → Analyze (RMS) → Math (gain) → Null CHOP (audio_data)
  Circle TOP (radius driven by audio) → Level TOP → Null TOP (OUTPUT)
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
    raise RuntimeError(
        f"Cannot create '{node_name}'. Tried: {attempts}\n"
        f"Add manually: right-click → Add Operator, search, rename to '{node_name}'."
    )


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

    # ── CHOP: audio analysis ──────────────────────────────────────────────────

    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP')
    audio.nodeX, audio.nodeY = -700, 100

    rms = create_op(p, 'analyze_rms', 'analyzeCHOP')
    rms.nodeX, rms.nodeY = -500, 100
    rms.par.function = 'rms'
    connect_op(rms, 0, audio)

    gain = create_op(p, 'math_gain', 'mathCHOP')
    gain.nodeX, gain.nodeY = -300, 100
    gain.par.gain = 5.0
    connect_op(gain, 0, rms)

    data = create_op(p, 'audio_data', 'nullCHOP')
    data.nodeX, data.nodeY = -100, 100
    connect_op(data, 0, gain)

    # ── TOP: visuals ──────────────────────────────────────────────────────────

    circle = create_op(p, 'circle_pulse', 'circleTOP')
    circle.nodeX, circle.nodeY = -500, -200
    circle.par.radiusx.expr = "min(0.45, max(0.05, op('audio_data')[0] * 0.4))"
    circle.par.radiusy.expr = "min(0.45, max(0.05, op('audio_data')[0] * 0.4))"
    circle.par.fillcolorr = 0.9
    circle.par.fillcolorg = 0.2
    circle.par.fillcolorb = 1.0

    level = create_op(p, 'level_brightness', 'levelTOP')
    level.nodeX, level.nodeY = -300, -200
    level.par.brightness1.expr = "0.4 + op('audio_data')[0] * 1.5"
    connect_op(level, 0, circle)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = -100, -200
    connect_op(output, 0, level)

    print("=" * 55)
    print("Network 01: Basic Volume Pulse — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Circle not moving: select math_gain, raise Gain (try 10–50)")
    print("=" * 55)


build()
