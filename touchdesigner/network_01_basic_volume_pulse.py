"""
Network 01: Basic Volume Pulse
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  1. In TouchDesigner, create a Base COMP (right-click network → Base)
  2. Double-click to go inside it
  3. Add a Text DAT inside (right-click → DAT → Text)
  4. Paste this entire script into the Text DAT
  5. Set Text DAT 'Language' parameter to 'Python'
  6. Right-click the Text DAT → Run Script
  7. Right-click the OUTPUT node → View

  If you get a NameError for any operator type, run this in the Textport (Alt+T)
  to see every available type name in your TD version:
    [x for x in dir() if x.endswith('CHOP')]
    [x for x in dir() if x.endswith('TOP')]
"""


def td_op(*names):
    """
    Looks up a TouchDesigner operator type by trying each name in turn.
    Tries globals(), locals(), and builtins — the same lookup Python uses
    for bare names, but wrapped in try/except so we can try alternatives.
    If nothing is found, prints diagnostics and raises NameError.
    """
    for name in names:
        try:
            result = eval(name)  # uses current frame: globals + locals + builtins
            if result is not None:
                return result
        except NameError:
            continue

    # Nothing worked — print something useful before failing
    chops = sorted(k for k in dir() if k.endswith('CHOP'))
    tops  = sorted(k for k in dir() if k.endswith('TOP'))
    print(f"\nERROR: operator type(s) not found: {names}")
    print(f"Run in the Textport to find correct names:")
    print(f"  [x for x in dir() if 'audio' in x.lower()]")
    print(f"Sample CHOPs visible right now: {chops[:6]}")
    print(f"Sample TOPs  visible right now: {tops[:6]}")
    raise NameError(f"None of these TD operator types were found: {names}")


def build():
    p = me.parent()   # Base COMP that contains this Text DAT

    # ── CHOP: Audio analysis ──────────────────────────────────────────────────

    audio = p.create(td_op('audiodevInCHOP'), 'audio_in')
    audio.nodeX, audio.nodeY = -700, 100
    # If 'audio_in' shows a red cook error after building:
    #   click it → Parameters → set Device to your microphone.

    rms = p.create(td_op('analyzeCHOP'), 'analyze_rms')
    rms.nodeX, rms.nodeY = -500, 100
    rms.par.function = 'rms'    # Root Mean Square ≈ perceived loudness
    rms.setInput(0, audio)

    # Math CHOP: amplify the tiny RMS values (often 0.001–0.05) into 0–1 range.
    # Increase 'gain' if the circle barely moves (try 10, 20, 50).
    gain = p.create(td_op('mathCHOP'), 'math_gain')
    gain.nodeX, gain.nodeY = -300, 100
    gain.par.gain = 5.0
    gain.setInput(0, rms)

    # Null CHOP: stable named reference that visual expressions can point at.
    data = p.create(td_op('nullCHOP'), 'audio_data')
    data.nodeX, data.nodeY = -100, 100
    data.setInput(0, gain)

    # ── TOP: Visuals ───────────────────────────────────────────────────────────

    # Circle TOP: radius expression drives size from audio loudness.
    # op('audio_data')[0] = current value of first channel (the RMS gain output).
    circle = p.create(td_op('circleTOP'), 'circle_pulse')
    circle.nodeX, circle.nodeY = -500, -200
    circle.par.radx.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.rady.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.colorr = 0.9
    circle.par.colorg = 0.2
    circle.par.colorb = 1.0    # purple-white fill

    # Level TOP: flash brighter on loud moments.
    level = p.create(td_op('levelTOP'), 'level_brightness')
    level.nodeX, level.nodeY = -300, -200
    level.par.brightness.expr = "0.4 + op('audio_data')[0] * 1.5"
    level.setInput(0, circle)

    output = p.create(td_op('nullTOP'), 'OUTPUT')
    output.nodeX, output.nodeY = -100, -200
    output.setInput(0, level)

    print("=" * 55)
    print("Network 01: Basic Volume Pulse — BUILT in", p.path)
    print()
    print("→ Right-click OUTPUT → View")
    print("→ If audio_in is red: click it, set Device to your mic")
    print("→ If circle doesn't move: select math_gain, raise Gain")
    print("  (try 10, 20, 50 depending on mic level)")
    print("=" * 55)


build()
