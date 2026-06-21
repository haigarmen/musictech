"""
Network 05: Real-Time Video Source Altered by Audio
=====================================================
A live webcam (or any video device) feed is transformed in real time by
three audio frequency bands. This is the culmination of the series:
a full AV performance tool where the camera image becomes an instrument.

    BASS  → Feedback depth  (kick drum = smear / ghosting)
    MID   → Hue rotation    (melodic content = color shifting)
    HIGH  → Displacement    (hi-hats / transients = pixel ripple / jitter)

Signal Flow:
    [Video Device In TOP] ──────────────────────────────────────┐
                                                                 ↓
    [Audio In] → [3 band analysis] ──────────────────────→ effect parameters
                                                                 │
    [Feedback TOP] → [Level (fade)] ─→ [Composite (add)]  ←─ [Noise Displace TOP]
                                                │                    ↑
                                         [Null: OUTPUT]      [HSV Adjust TOP]
                                                                     ↑
                                                            [Displace TOP]
                                                                     ↑
                                                        [Video Device In TOP]

Detailed effects chain:
    Video In → Displace (high band ripple) → HSV Adjust (mid band hue)
            → Composite over Feedback trail (bass band depth) → OUTPUT

Concepts introduced:
    - Video Device In TOP: live webcam or capture card input
    - Displace TOP: pixel displacement map (noise-based ripple effect)
    - HSV Adjust TOP: hue rotation driven by mid frequencies
    - Layering all previous techniques (feedback, glow, multi-band analysis)
    - Combining a real video signal with procedural effects

How to run:
    1. Connect a webcam or select a video capture device.
    2. Paste into a Text DAT inside a Base COMP and Run Script.
    3. After building, select 'video_in' and set the correct device index.
"""

BUILD_PATH = '/project1'

# Change this index to match your webcam (0 = first camera, 1 = second, etc.)
VIDEO_DEVICE_INDEX = 0


def build():
    p = op(BUILD_PATH)
    if p is None:
        print(f"ERROR: '{BUILD_PATH}' not found.")
        return

    # ── Audio analysis (3 bands) ──────────────────────────────────────────────
    # Identical to Networks 03 & 04.

    audio_in = p.create(audiodevInCHOP, 'audio_in')
    audio_in.nodeX, audio_in.nodeY = -1400, 800
    audio_in.par.rate = 44100

    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -1200, 800
    spectrum.par.windowsize = 512
    spectrum.par.overlap    = 0.75
    spectrum.setInput(0, audio_in)

    band_defs = [
        ('bass',  0,   10, -1000, 1000),
        ('mid',   10,  60, -1000,  800),
        ('high',  60, 200, -1000,  600),
    ]
    nulls = {}
    for name, ch_start, ch_end, nx, ny in band_defs:
        sel = p.create(selectCHOP, f'select_{name}')
        sel.nodeX, sel.nodeY = nx, ny
        sel.par.chanstart = ch_start
        sel.par.chanend   = ch_end - 1
        sel.setInput(0, spectrum)

        analyze = p.create(analyzeCHOP, f'analyze_{name}')
        analyze.nodeX, analyze.nodeY = nx + 200, ny
        analyze.par.function = 'average'
        analyze.setInput(0, sel)

        filt = p.create(filterCHOP, f'filter_{name}')
        filt.nodeX, filt.nodeY = nx + 400, ny
        filt.par.width = 0.04
        filt.setInput(0, analyze)

        math = p.create(mathCHOP, f'math_{name}')
        math.nodeX, math.nodeY = nx + 600, ny
        math.par.gain  = 14.0
        math.par.clamp = True
        math.par.clampmin = 0.0
        math.par.clampmax = 1.0
        math.setInput(0, filt)

        null = p.create(nullCHOP, f'data_{name}')
        null.nodeX, null.nodeY = nx + 800, ny
        null.setInput(0, math)
        nulls[name] = null

    # ── Live video source ─────────────────────────────────────────────────────

    vid_in = p.create(videodevInTOP, 'video_in')
    vid_in.nodeX, vid_in.nodeY = -600, 200
    vid_in.par.device = VIDEO_DEVICE_INDEX
    # Resolution: set to match your camera; 1280×720 is a safe default
    vid_in.par.resolutionw = 1280
    vid_in.par.resolutionh = 720

    # ── Effect 1: Displacement (HIGH band → pixel ripple) ────────────────────
    # A noise texture is used as the displacement map.
    # High frequencies (hi-hats, transients) cause the image to shimmer.

    disp_noise = p.create(noiseTOP, 'disp_noise')
    disp_noise.nodeX, disp_noise.nodeY = -600, 0
    # Noise animates slowly at rest; high band adds fast chaotic motion
    disp_noise.par.tx.expr     = "absTime.seconds * 0.1"
    disp_noise.par.ty.expr     = "absTime.seconds * 0.07"
    disp_noise.par.periodx.expr = "0.4 + op('data_high')['chan1'] * 0.3"
    disp_noise.par.amp.expr    = "0.5"

    displace = p.create(displaceTOP, 'displace')
    displace.nodeX, displace.nodeY = -400, 200
    # Displacement amount: quiet = tiny wobble, high transients = hard jitter
    displace.par.displacex.expr = "0.002 + op('data_high')['chan1'] * 0.05"
    displace.par.displacey.expr = "0.002 + op('data_high')['chan1'] * 0.05"
    displace.setInput(0, vid_in)       # source image
    displace.setInput(1, disp_noise)   # displacement map

    # ── Effect 2: HSV color shift (MID band → hue rotation) ──────────────────
    # Mid-range frequencies (vocals, synths, guitar) rotate the color palette.
    # At rest the video looks mostly natural; melodic content shifts colors.

    hsv = p.create(hsvAdjustTOP, 'hsv_shift')
    hsv.nodeX, hsv.nodeY = -200, 200
    # Slow continuous hue drift + fast jumps on mid hits
    hsv.par.hue.expr        = "absTime.seconds * 0.03 % 1.0 + op('data_mid')['chan1'] * 0.45"
    hsv.par.saturation.expr = "1.0 + op('data_mid')['chan1']  * 0.8"   # oversaturate on melody
    hsv.par.value.expr      = "0.8 + op('data_bass')['chan1'] * 0.4"   # bass brightens image
    hsv.setInput(0, displace)

    # ── Effect 3: Feedback trail (BASS band → ghosting depth) ────────────────
    # Kick drums and bass hits cause the previous frames to linger visibly.
    # At silence the image is crisp; on bass drops it smears into itself.

    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = -200, 0

    # Fade: 0.0 = instant decay, 1.0 = frames never fade
    # Bass hit → raise toward 0.94 so previous frame lingers
    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = 0, 0
    fade.par.brightness.expr = "0.60 + op('data_bass')['chan1'] * 0.34"
    fade.setInput(0, feedback)

    # Mix current processed frame with faded history
    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 0, 200
    comp_fb.par.operand = 'over'       # 'over' keeps video dominant; try 'add' for glow
    comp_fb.setInput(0, fade)          # faded history behind
    comp_fb.setInput(1, hsv)           # current frame in front

    # Close the feedback loop
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    # Subtle glow that blooms on bass hits
    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 200, 200
    glow.par.size.expr     = "2 + op('data_bass')['chan1'] * 25"
    glow.par.strength.expr = "0.1 + op('data_bass')['chan1'] * 0.8"
    glow.setInput(0, comp_fb)

    # Level: push contrast/gamma so the final image reads well on a projector
    level_out = p.create(levelTOP, 'level_output')
    level_out.nodeX, level_out.nodeY = 400, 200
    level_out.par.brightness = 1.0
    level_out.par.contrast   = 1.1
    level_out.par.gamma      = 0.95
    level_out.setInput(0, glow)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 600, 200
    output.setInput(0, level_out)

    print("✓  Network 05 built.")
    print("")
    print("   Effects summary:")
    print("     BASS  → feedback trail depth (ghosting on kick/bass hits)")
    print("     MID   → hue rotation + saturation (color shifts on melody)")
    print("     HIGH  → pixel displacement (image ripples on transients)")
    print("")
    print("   TIP: Select 'video_in' and set the correct device index for your camera.")
    print("   TIP: If no camera, replace 'video_in' with a Movie File In TOP.")
    print("   TIP: Adjust math_bass/mid/high 'Gain' to calibrate to your signal level.")
    print("   TIP: Try changing comp_feedback 'Operand' from 'over' to 'add' for a")
    print("        bright, accumulating look instead of a trail/ghost look.")

build()
