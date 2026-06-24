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
    """
    Create a TD operator using string-based creation (confirmed working in TD 2025+).
    Tries each provided type name, then auto-tries an all-lowercase variant
    of the operator-name part (e.g. hsvAdjustTOP → hsvadjustTOP).
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

    # ── CHOP: audio analysis ──────────────────────────────────────────────────

    # TD 2025 name: audiodeviceinCHOP  (older builds: audiodevInCHOP)
    audio = create_op(p, 'audio_in', 'audiodeviceinCHOP', 'audiodevInCHOP')
    audio.nodeX, audio.nodeY = -700, 100
    # If 'audio_in' shows a red cook error: click it → Parameters → pick Device.

    rms = create_op(p, 'analyze_rms', 'analyzeCHOP')
    rms.nodeX, rms.nodeY = -500, 100
    rms.par.function = 'rms'
    rms.setInput(0, audio)

    # Increase Gain if the circle barely reacts (try 10, 20, 50).
    gain = create_op(p, 'math_gain', 'mathCHOP')
    gain.nodeX, gain.nodeY = -300, 100
    gain.par.gain = 5.0
    gain.setInput(0, rms)

    data = create_op(p, 'audio_data', 'nullCHOP')
    data.nodeX, data.nodeY = -100, 100
    data.setInput(0, gain)

    # ── TOP: visuals ──────────────────────────────────────────────────────────

    # Radius grows from 0.05 (silence) to 0.45 (full volume).
    circle = create_op(p, 'circle_pulse', 'circleTOP')
    circle.nodeX, circle.nodeY = -500, -200
    circle.par.radx.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.rady.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.colorr = 0.9
    circle.par.colorg = 0.2
    circle.par.colorb = 1.0

    level = create_op(p, 'level_brightness', 'levelTOP')
    level.nodeX, level.nodeY = -300, -200
    level.par.brightness.expr = "0.4 + op('audio_data')[0] * 1.5"
    level.setInput(0, circle)

    output = create_op(p, 'OUTPUT', 'nullTOP')
    output.nodeX, output.nodeY = -100, -200
    output.setInput(0, level)

    print("=" * 55)
    print("Network 01: Basic Volume Pulse — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Circle not moving: select math_gain, raise Gain")
    print("  (try 10, 20, 50 depending on your mic level)")
    print("=" * 55)


build()
