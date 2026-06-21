"""
Network 01: Basic Volume Pulse
===============================
The simplest audio-reactive graphic: a circle that grows and glows
with the overall loudness (RMS) of the incoming audio signal.

Signal Flow:
    [Audio Device In] → [Analyze RMS] → [Filter] → [Math] → [Null CHOP]
                                                                    ↓
    [Constant BG] → [Composite] ← [Circle TOP (radius = f(volume))]
                         ↓
                    [Level TOP (brightness = f(volume))] → [Null TOP: OUTPUT]

Concepts introduced:
    - Audio Device In CHOP: captures live microphone or line input
    - Analyze CHOP: reduces a signal to a single scalar (RMS = energy)
    - Filter CHOP: smooths jitter for organic motion
    - Math CHOP: remaps a signal to a useful visual range
    - Parameter expressions: linking a CHOP value to a TOP parameter

How to run:
    1. Create a Base COMP in your project (e.g. /project1/base1)
    2. Inside it, create a Text DAT and paste this script
    3. Set the Text DAT "Language" to Python, then right-click → Run Script
    OR paste directly into the Textport (Alt+T) after setting BUILD_PATH below.
"""

# ---------- configuration ----------
BUILD_PATH = '/project1'   # path to the container where the network will be built
# -----------------------------------


def build():
    p = op(BUILD_PATH)
    if p is None:
        print(f"ERROR: '{BUILD_PATH}' not found. Create a Base COMP there first.")
        return

    # ── Audio chain ─────────────────────────────────────────────────────────

    audio_in = p.create(audiodevInCHOP, 'audio_in')
    audio_in.nodeX, audio_in.nodeY = -900, 200
    # 'device 0' = system default input; change index to select another device
    audio_in.par.rate = 44100

    # RMS analysis: Root Mean Square = perceptual loudness of the signal
    analyze = p.create(analyzeCHOP, 'analyze_rms')
    analyze.nodeX, analyze.nodeY = -700, 200
    analyze.par.function = 'rms'
    analyze.setInput(0, audio_in)

    # Smooth rapid transients so the circle moves organically, not jerkily
    filt = p.create(filterCHOP, 'filter_smooth')
    filt.nodeX, filt.nodeY = -500, 200
    filt.par.width = 0.04       # 40 ms lag — adjust for faster/slower response
    filt.setInput(0, analyze)

    # Remap 0..0.5 → 0..1 so quiet rooms still show some movement
    math = p.create(mathCHOP, 'math_remap')
    math.nodeX, math.nodeY = -300, 200
    math.par.fromrangex = 0.0   # input min
    math.par.fromrangey = 0.5   # input max (tune to your loudest signal)
    math.par.torangex   = 0.0   # output min
    math.par.torangey   = 1.0   # output max
    math.setInput(0, filt)

    # Null CHOP: a stable reference other operators can point their expressions at
    audio_data = p.create(nullCHOP, 'audio_data')
    audio_data.nodeX, audio_data.nodeY = -100, 200
    audio_data.setInput(0, math)

    # ── Visuals ──────────────────────────────────────────────────────────────

    # Very dark background so the bright circle pops
    bg = p.create(constTOP, 'bg')
    bg.nodeX, bg.nodeY = -900, -100
    bg.par.colorr = 0.02
    bg.par.colorg = 0.02
    bg.par.colorb = 0.06

    # Circle whose radius tracks audio loudness
    circle = p.create(circleTOP, 'circle_pulse')
    circle.nodeX, circle.nodeY = -700, -100
    # Base radius 0.05 (5% of frame) + up to 0.38 more at full volume
    circle.par.radx.expr = "0.05 + op('audio_data')['chan1'] * 0.38"
    circle.par.rady.expr = "0.05 + op('audio_data')['chan1'] * 0.38"
    circle.par.colorr = 0.85
    circle.par.colorg = 0.20
    circle.par.colorb = 1.00    # purple-white

    # Place circle over background
    comp = p.create(compositeTOP, 'composite')
    comp.nodeX, comp.nodeY = -500, -100
    comp.par.operand = 'over'
    comp.setInput(0, bg)
    comp.setInput(1, circle)

    # Boost brightness on loud moments for an energy "flash" feel
    level = p.create(levelTOP, 'level_boost')
    level.nodeX, level.nodeY = -300, -100
    level.par.brightness.expr = "0.7 + op('audio_data')['chan1'] * 0.8"
    level.par.contrast.expr   = "1.0 + op('audio_data')['chan1'] * 0.4"
    level.setInput(0, comp)

    # Final output node — view this to see the result
    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = -100, -100
    output.setInput(0, level)

    print("✓  Network 01 built.  Right-click 'OUTPUT' → View to see the result.")
    print("   Speak or play music into your microphone to test.")

build()
