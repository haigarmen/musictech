"""
Network 01: Basic Volume Pulse
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  1. In your TouchDesigner project, create a Base COMP (right-click in network → Base)
  2. Double-click to go inside it
  3. Add a Text DAT (right-click → Add Operator → DAT → Text)
  4. Paste this entire script into the Text DAT
  5. Set the Text DAT 'Language' parameter to 'Python'
  6. Right-click the Text DAT → Run Script
  7. Right-click the OUTPUT node that appears → View

WHAT GETS BUILT:
  Audio Device In → Analyze RMS → Math (gain) → Null CHOP (audio_data)
  Circle TOP (radius driven by audio_data) → Level TOP → Null TOP (OUTPUT)

TROUBLESHOOTING:
  • 'audio_in' cook error / no device: click 'audio_in', open its parameters,
    go to the Audio Device page and select your microphone from the Device menu.
  • Circle doesn't react: select 'math_gain' and increase its Gain parameter.
    Start at 5, go up to 20+ for a quiet mic.
  • Wrong operator type error: your TD version may use a different internal name.
    Open the OP Create dialog (Tab key), search for the operator, and note its
    exact name — then replace the type constant in this script.
"""


def build():
    # 'me' is this Text DAT; me.parent() is the Base COMP it lives inside.
    # The whole network is built inside that same Base COMP.
    p = me.parent()

    # ── CHOP chain: capture and measure audio loudness ────────────────────────

    # Audio Device In: captures the live microphone or line input
    audio = p.create(audiodevInCHOP, 'audio_in')
    audio.nodeX, audio.nodeY = -700, 100
    # TD will try to use the default audio device.
    # If this shows a cook error, select it and pick your device manually.

    # Analyze CHOP: collapses the audio waveform into a single RMS value.
    # RMS (Root Mean Square) approximates perceived loudness.
    rms = p.create(analyzeCHOP, 'analyze_rms')
    rms.nodeX, rms.nodeY = -500, 100
    rms.par.function = 'rms'
    rms.setInput(0, audio)

    # Math CHOP: multiply the tiny RMS values (often 0.001–0.1) to a usable range.
    gain = p.create(mathCHOP, 'math_gain')
    gain.nodeX, gain.nodeY = -300, 100
    gain.par.gain = 5.0    # ← TUNE THIS. Increase if signal is too quiet.
    gain.setInput(0, rms)

    # Null CHOP: stable reference point. All visual expressions point here.
    data = p.create(nullCHOP, 'audio_data')
    data.nodeX, data.nodeY = -100, 100
    data.setInput(0, gain)

    # ── TOP chain: draw the audio-reactive visual ─────────────────────────────

    # Circle TOP: radius is driven by audio_data channel 0 (the RMS value).
    # [0] = first channel, 0-indexed. At silence radius ~0.05, at full volume ~0.45.
    circle = p.create(circleTOP, 'circle_pulse')
    circle.nodeX, circle.nodeY = -500, -150
    circle.par.radx.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.rady.expr = "clamp(op('audio_data')[0] * 0.4, 0.05, 0.45)"
    circle.par.colorr = 0.9
    circle.par.colorg = 0.2
    circle.par.colorb = 1.0    # purple-white fill

    # Level TOP: boosts brightness on loud moments for an energy-flash feel.
    level = p.create(levelTOP, 'level_brightness')
    level.nodeX, level.nodeY = -300, -150
    level.par.brightness.expr = "0.4 + op('audio_data')[0] * 1.5"
    level.setInput(0, circle)

    # OUTPUT: right-click this and choose View to see the result.
    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = -100, -150
    output.setInput(0, level)

    print("=" * 50)
    print("Network 01: Basic Volume Pulse — BUILT")
    print("Container:", p.path)
    print()
    print("Next steps:")
    print("  1. Right-click OUTPUT → View")
    print("  2. If 'audio_in' shows a red cook error:")
    print("     Click it → Parameters → select your mic from Device")
    print("  3. If circle doesn't move: select 'math_gain'")
    print("     and increase the Gain value (try 10, 20, 50...)")
    print("=" * 50)


build()
