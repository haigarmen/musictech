"""
Network 01: Basic Volume Pulse
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  1. In TouchDesigner, right-click in the network → Base (creates a Base COMP)
  2. Double-click the Base COMP to go inside it
  3. Right-click inside → DAT → Text
  4. Paste this entire script, set Language = Python, Run Script
  5. Right-click the OUTPUT node → View

IF YOU GET A NameError:
  Run diagnose.py first (same folder) to see what operator type names are
  available in your specific TD build.
"""

import builtins as _bt

try:
    import td as _td
except Exception:
    _td = None


def td_op(*names):
    """
    Look up a TouchDesigner operator type constant without using eval().
    Searches globals(), builtins, and td module — all via safe dict/attr
    lookups that never raise exceptions — then tries string-based creation
    as a last resort.
    """
    g = globals()
    for name in names:
        # 1. Script-level globals (where TD normally injects OP type constants)
        t = g.get(name)
        if t is not None:
            return t
        # 2. Python builtins module
        t = getattr(_bt, name, None)
        if t is not None:
            return t
        # 3. The td module itself
        if _td is not None:
            t = getattr(_td, name, None)
            if t is not None:
                return t
    # Return a sentinel that create_op() will interpret as "use string fallback"
    return names[0]   # pass the string name; create_op() will try it as a string


def create_op(parent_comp, type_name, node_name):
    """
    Create a TD operator. Tries the type constant first, then the bare
    string name (without CHOP/TOP suffix), then the full string name.
    """
    op_type = td_op(type_name)

    # If td_op found a real type object, use it
    if not isinstance(op_type, str):
        try:
            return parent_comp.create(op_type, node_name)
        except Exception:
            pass  # fall through to string methods

    # String fallback — strip the family suffix for the short form
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
        f"Cannot create operator '{type_name}'.\n"
        f"Add it manually inside the Base COMP: right-click → Add Operator.\n"
        f"Then search for '{short}' and rename the result to '{node_name}'.\n"
        f"Run diagnose.py for more information."
    )


def build():
    p = me.parent()

    # ── CHOP: audio analysis ──────────────────────────────────────────────────

    audio = create_op(p, 'audiodevInCHOP', 'audio_in')
    audio.nodeX, audio.nodeY = -700, 100
    # If 'audio_in' shows a red cook error: click it → Parameters → pick Device.

    rms = create_op(p, 'analyzeCHOP', 'analyze_rms')
    rms.nodeX, rms.nodeY = -500, 100
    rms.par.function = 'rms'
    rms.setInput(0, audio)

    # Increase 'gain' if the circle barely reacts (try 10, 20, 50).
    gain = create_op(p, 'mathCHOP', 'math_gain')
    gain.nodeX, gain.nodeY = -300, 100
    gain.par.gain = 5.0
    gain.setInput(0, rms)

    data = create_op(p, 'nullCHOP', 'audio_data')
    data.nodeX, data.nodeY = -100, 100
    data.setInput(0, gain)

    # ── TOP: visuals ──────────────────────────────────────────────────────────

    circle = create_op(p, 'circleTOP', 'circle_pulse')
    circle.nodeX, circle.nodeY = -500, -200
    circle.par.radx.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.rady.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.colorr = 0.9
    circle.par.colorg = 0.2
    circle.par.colorb = 1.0

    level = create_op(p, 'levelTOP', 'level_brightness')
    level.nodeX, level.nodeY = -300, -200
    level.par.brightness.expr = "0.4 + op('audio_data')[0] * 1.5"
    level.setInput(0, circle)

    output = create_op(p, 'nullTOP', 'OUTPUT')
    output.nodeX, output.nodeY = -100, -200
    output.setInput(0, level)

    print("=" * 55)
    print("Network 01: Basic Volume Pulse — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ audio_in red: click it → Parameters → pick your mic")
    print("→ Circle not moving: select math_gain, raise Gain")
    print("  (try 10, 20, 50 for your mic level)")
    print("=" * 55)


build()
