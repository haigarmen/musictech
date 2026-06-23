"""
Network 05: Real-Time Video Source Altered by Audio
Audio-Reactive Motion Graphics — TouchDesigner Network Builder

HOW TO RUN:
  Same as Network 01 — paste into a Text DAT inside a Base COMP, Run Script.
  Connect a webcam before running. If no webcam is available, see the
  'USING A VIDEO FILE INSTEAD' note at the bottom.

WHAT GETS BUILT:
  Video Device In TOP (webcam) ─────────────────────────────────────┐
                                                                      ↓
  Audio In → Spectrum → band expressions ─→ Displace TOP (high band)
                                            → HSV Adjust (mid band hue)
                                            → Composite + Feedback (bass trails)
                                            → Glow → Level → Null TOP (OUTPUT)

THREE-BAND EFFECTS ON THE VIDEO:
  BASS  → Feedback depth. On kick drum hits, previous frames linger as ghost trails.
           Silence = crisp image. Hard bass = heavy smear.
  MID   → Hue rotation + saturation boost. Melodic content shifts the color palette.
           Sustained notes cycle through rainbow. Stabs snap to a new color.
  HIGH  → Pixel displacement. A noise texture shifts pixels sideways/vertically.
           Hi-hats and transients cause the image to ripple and jitter.

AFTER BUILDING:
  1. Select 'video_in' and set Device to your webcam index (0 = first camera).
  2. Right-click OUTPUT → View.
  3. Tune the gain multipliers in the BASS/MID/HIGH expressions if needed.

USING A VIDEO FILE INSTEAD OF A WEBCAM:
  Delete 'video_in' after building, add a Movie File In TOP, name it 'video_in',
  point it at a video file, and set it to Loop. Everything else stays the same.
"""

# Index of your webcam. 0 = first camera in the system. Change if needed.
VIDEO_DEVICE_INDEX = 0


def build():
    p = me.parent()

    # ── Audio + spectrum ──────────────────────────────────────────────────────

    audio = p.create(audiodevInCHOP, 'audio_in')
    audio.nodeX, audio.nodeY = -1000, 500

    spectrum = p.create(spectrumCHOP, 'spectrum')
    spectrum.nodeX, spectrum.nodeY = -800, 500
    spectrum.par.windowsize = 512
    spectrum.setInput(0, audio)

    spec_data = p.create(nullCHOP, 'spectrum_data')
    spec_data.nodeX, spec_data.nodeY = -600, 500
    spec_data.setInput(0, spectrum)

    # Band energy expressions — tune the multipliers for your signal level
    BASS  = "clamp((op('spectrum_data')[1]+op('spectrum_data')[2]+op('spectrum_data')[3]+op('spectrum_data')[4]) * 60, 0, 1)"
    MID   = "clamp((op('spectrum_data')[15]+op('spectrum_data')[25]+op('spectrum_data')[35]) * 90, 0, 1)"
    HIGH  = "clamp((op('spectrum_data')[60]+op('spectrum_data')[90]+op('spectrum_data')[120]) * 120, 0, 1)"

    # ── Live video source ─────────────────────────────────────────────────────

    vid = p.create(videodevInTOP, 'video_in')
    vid.nodeX, vid.nodeY = -600, 100
    vid.par.device = VIDEO_DEVICE_INDEX
    # Select 'video_in' and confirm your camera appears in the Device parameter.
    # If the image is wrong resolution: set width/height manually in parameters.

    # ── Effect 1: Pixel displacement driven by HIGH band ─────────────────────
    # A slowly-moving noise texture acts as a displacement map.
    # High-frequency transients (hi-hats, claps) increase the displacement amount,
    # making the video image appear to ripple or shatter.

    disp_noise = p.create(noiseTOP, 'disp_noise')
    disp_noise.nodeX, disp_noise.nodeY = -600, -100
    disp_noise.par.tx.expr = "absTime.seconds * 0.15"
    disp_noise.par.ty.expr = "absTime.seconds * 0.09"
    # High band pushes noise into finer, faster detail
    disp_noise.par.rough.expr = f"0.5 + ({HIGH}) * 0.45"

    displace = p.create(displaceTOP, 'displace_high')
    displace.nodeX, displace.nodeY = -400, 100
    # Displacement strength: whisper-quiet = tiny wobble, transient = hard jitter
    displace.par.displacex.expr = f"0.003 + ({HIGH}) * 0.06"
    displace.par.displacey.expr = f"0.003 + ({HIGH}) * 0.04"
    displace.setInput(0, vid)         # image to distort
    displace.setInput(1, disp_noise)  # displacement map

    # ── Effect 2: Hue rotation driven by MID band ─────────────────────────────
    # Mid-range content (vocals, synths, guitar chords) rotates the color palette.
    # At rest the image looks natural; on melodic hits it shifts to vivid colors.

    hsv = p.create(hsvAdjustTOP, 'hsv_shift')
    hsv.nodeX, hsv.nodeY = -200, 100
    # Hue slowly drifts over time; mid energy adds fast jump shifts
    hsv.par.hue.expr        = f"(absTime.seconds * 0.02 + ({MID}) * 0.5) % 1.0"
    # Saturation boost: mid energy oversaturates the image
    hsv.par.saturation.expr = f"1.0 + ({MID}) * 0.9"
    # Value (brightness): bass raises overall brightness
    hsv.par.value.expr      = f"0.85 + ({BASS}) * 0.3"
    hsv.setInput(0, displace)

    # ── Effect 3: Feedback trail driven by BASS band ──────────────────────────
    # The Feedback TOP reads the previous composite frame.
    # On bass hits, the fade factor approaches 1.0 → old frames linger visibly.
    # In silence the value stays low → image stays crisp with minimal trailing.

    feedback = p.create(feedbackTOP, 'feedback')
    feedback.nodeX, feedback.nodeY = -200, -100

    # Each frame: dim history by this factor before compositing current frame over it.
    # 0.60 = fast fade (crisp). 0.94 = slow fade (heavy trails).
    fade = p.create(levelTOP, 'feedback_fade')
    fade.nodeX, fade.nodeY = 0, -100
    fade.par.brightness.expr = f"0.60 + ({BASS}) * 0.34"
    fade.setInput(0, feedback)

    # Current processed frame composited over faded history.
    # 'over' keeps video dominant; try 'add' for a bright accumulating glow look.
    comp_fb = p.create(compositeTOP, 'comp_feedback')
    comp_fb.nodeX, comp_fb.nodeY = 0, 100
    comp_fb.par.operand = 'over'
    comp_fb.setInput(0, fade)   # faded history (behind)
    comp_fb.setInput(1, hsv)    # current color-shifted frame (in front)

    # Close the feedback loop — point Feedback TOP at the composite node
    feedback.par.top = comp_fb.name

    # ── Post-processing ───────────────────────────────────────────────────────

    # Glow blooms on bass hits: kicks and low ends create a halo effect
    glow = p.create(glowTOP, 'glow')
    glow.nodeX, glow.nodeY = 200, 100
    glow.par.size.expr     = f"1 + ({BASS}) * 25"
    glow.par.strength.expr = f"0.05 + ({BASS}) * 0.7"
    glow.setInput(0, comp_fb)

    # Final level adjustment: pull back any blown-out brightness from feedback
    level_out = p.create(levelTOP, 'level_output')
    level_out.nodeX, level_out.nodeY = 400, 100
    level_out.par.brightness = 1.0
    level_out.par.contrast   = 1.1
    level_out.par.gamma      = 0.9
    level_out.setInput(0, glow)

    output = p.create(nullTOP, 'OUTPUT')
    output.nodeX, output.nodeY = 600, 100
    output.setInput(0, level_out)

    print("=" * 50)
    print("Network 05: Video + Audio — BUILT")
    print("Container:", p.path)
    print()
    print("SETUP:")
    print("  1. Select 'video_in' → set Device to your webcam")
    print("  2. Right-click OUTPUT → View")
    print()
    print("WHAT TO LISTEN FOR:")
    print("  BASS beats → ghost/smear trails on the video")
    print("  MID melody → color palette shifts through hues")
    print("  HIGH transients → image ripples and jitters")
    print()
    print("QUICK TUNING:")
    print("  More reaction → increase ×60/×90/×120 in band expressions")
    print("  Longer trails → raise feedback_fade brightness upper bound")
    print("  More color → raise saturation expression multiplier in hsv_shift")
    print("=" * 50)


build()
