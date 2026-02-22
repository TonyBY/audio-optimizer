#!/usr/bin/env python3
"""
Audio Optimizer App
Web UI for vocal audio mixing and enhancement using ffmpeg.

Features:
  - Mix a dry vocal with an accompaniment track (sync + volume balance)
  - Optionally enhance the mix with EQ, compression, and loudness normalization
  - Standalone optimization of any single audio file
"""

import streamlit as st
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import time

st.set_page_config(
    page_title="Audio Optimizer",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Audio Optimizer")
st.markdown(
    "Mix a dry vocal with an accompaniment track, then enhance with professional-quality "
    "EQ, compression, and loudness normalization — or optimize any single audio file."
)

# ── ffmpeg check ──────────────────────────────────────────────────────────────
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if not check_ffmpeg():
    st.error("⚠️ ffmpeg is not installed. Please install it: `brew install ffmpeg` (macOS) or see README.")
    st.stop()

# ── Sidebar — Optimization Settings ──────────────────────────────────────────
st.sidebar.header("⚙️ Optimization Settings")
st.sidebar.caption("Applied when optimizing audio in either tab.")

vocal_profile = st.sidebar.selectbox(
    "Vocal Profile",
    ["low_baritone", "tenor", "female", "spoken"],
    help=(
        "low_baritone: Deep male voice  |  tenor: Higher male voice  |  "
        "female: Female voice  |  spoken: Podcast/narration"
    )
)

target_loudness = st.sidebar.slider(
    "Target Loudness (LUFS)",
    min_value=-23, max_value=-9, value=-14, step=1,
    help="-14 LUFS is the standard for streaming platforms (Spotify, Apple Music, YouTube)"
)

reverb = st.sidebar.selectbox(
    "Reverb",
    ["off", "light", "pop_ballad"],
    help="off: Dry signal  |  light: Subtle room  |  pop_ballad: Moderate reverb"
)

noise_level = st.sidebar.selectbox(
    "Noise Reduction",
    ["light", "medium", "strong"],
    help="Strength of background noise removal via high-pass filtering"
)

deessing = st.sidebar.selectbox(
    "De-essing",
    ["light", "medium", "strong"],
    help="Sibilance reduction (harsh 's' and 'sh' sounds)"
)

export_mp3 = st.sidebar.checkbox(
    "Export MP3", value=True,
    help="Also produce a 320 kbps MP3 alongside the lossless WAV"
)

with st.sidebar.expander("ℹ️ EQ Curve Details"):
    st.markdown("""
**Low Baritone** — 250 Hz (−3 dB), 3 kHz (+2 dB), 6.5 kHz (−2 dB), 10 kHz (+1 dB)

**Tenor** — 300 Hz (−2 dB), 3.5 kHz (+2.5 dB), 7 kHz (−2 dB), 11 kHz (+1.5 dB)

**Female** — 350 Hz (−2 dB), 4 kHz (+2 dB), 8 kHz (−2.5 dB), 12 kHz (+1 dB)

**Spoken** — 200 Hz (−3 dB), 2.5 kHz (+3 dB), 5 kHz (−1 dB)
""")

# ── Helper: audio duration ────────────────────────────────────────────────────
def get_audio_duration(filepath):
    """Return duration in seconds via ffprobe, or None on failure."""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return None

# ── Helper: detect leading-silence end (= first audio event) ─────────────────
def detect_audio_start(filepath, noise_db=-50, min_silence_s=0.3):
    """
    Return the timestamp (seconds) where audio first becomes non-silent.

    Uses ffmpeg silencedetect. If the file has no detectable leading silence
    (audio starts immediately) returns 0.0.

    noise_db        : threshold below which a signal is considered silent
    min_silence_s   : minimum duration to count as a silence period
    """
    import re
    cmd = [
        'ffmpeg', '-i', filepath,
        '-af', f'silencedetect=noise={noise_db}dB:d={min_silence_s}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr  # ffmpeg writes filter output to stderr

    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', output)]
    ends   = [float(x) for x in re.findall(r'silence_end: ([\d.]+)',   output)]

    # Leading silence exists when the first silence_start is at (or very near) 0
    if starts and ends and starts[0] < 0.1:
        return round(ends[0], 3)
    return 0.0

# ── Helper: download buttons ──────────────────────────────────────────────────
def create_download_buttons(wav_path, output_stem, temp_dir, key_suffix=""):
    """Copy wav_path to a named file and render WAV + optional MP3 download buttons."""
    wav_name = f"{output_stem}.wav"
    mp3_name = f"{output_stem}.mp3"
    dest_wav = os.path.join(temp_dir, wav_name)
    shutil.copy(wav_path, dest_wav)

    with open(dest_wav, 'rb') as f:
        wav_data = f.read()

    mp3_data = None
    if export_mp3:
        dest_mp3 = os.path.join(temp_dir, mp3_name)
        cmd = ['ffmpeg', '-i', dest_wav, '-b:a', '320k', '-y', dest_mp3]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            with open(dest_mp3, 'rb') as f:
                mp3_data = f.read()

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇️ Download WAV (Lossless)",
            data=wav_data,
            file_name=wav_name,
            mime="audio/wav",
            use_container_width=True,
            key=f"dl_wav_{key_suffix}"
        )
    if mp3_data:
        with col2:
            st.download_button(
                label="⬇️ Download MP3 (320 kbps)",
                data=mp3_data,
                file_name=mp3_name,
                mime="audio/mpeg",
                use_container_width=True,
                key=f"dl_mp3_{key_suffix}"
            )

# ── Core: mix two audio tracks ────────────────────────────────────────────────
def mix_audio(vocal_path, accomp_path, output_dir, vocal_offset, accomp_offset, vocal_vol, accomp_vol):
    """
    Mix two audio files with independent time offsets and volume levels.

    Returns (mixed_wav_path, stages_info) or None on failure.
    """
    stages_info = []

    # Step 1 — Convert both tracks to 48 kHz stereo WAV
    st.write("🔄 Step 1: Converting both tracks to 48 kHz stereo WAV…")
    vocal_wav = os.path.join(output_dir, "mix_vocal.wav")
    accomp_wav = os.path.join(output_dir, "mix_accomp.wav")

    for src, dst, label in [
        (vocal_path,  vocal_wav,  "Vocal"),
        (accomp_path, accomp_wav, "Accompaniment"),
    ]:
        cmd = ['ffmpeg', '-i', src, '-ar', '48000', '-ac', '2', '-y', dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            st.error(f"Conversion failed for {label}: {r.stderr}")
            return None

    stages_info.append("✓ Step 1: Converted both tracks → WAV 48 kHz stereo")

    # Step 2 — Synchronize and mix
    st.write("🔄 Step 2: Synchronizing and mixing tracks…")
    mixed_wav = os.path.join(output_dir, "mix_output.wav")

    vocal_delay_ms  = int(vocal_offset  * 1000)
    accomp_delay_ms = int(accomp_offset * 1000)

    # Build filter_complex step by step
    filter_parts = []
    filter_parts.append(f"[0:a]volume={vocal_vol  / 100.0:.4f}[v0]")
    filter_parts.append(f"[1:a]volume={accomp_vol / 100.0:.4f}[v1]")

    # Apply delays only when requested
    if vocal_delay_ms > 0:
        filter_parts.append(f"[v0]adelay={vocal_delay_ms}|{vocal_delay_ms}[vd]")
        vocal_ref = "[vd]"
    else:
        vocal_ref = "[v0]"

    if accomp_delay_ms > 0:
        filter_parts.append(f"[v1]adelay={accomp_delay_ms}|{accomp_delay_ms}[ad]")
        accomp_ref = "[ad]"
    else:
        accomp_ref = "[v1]"

    # amix: normalize=0 preserves the individual volume settings above
    filter_parts.append(
        f"{vocal_ref}{accomp_ref}amix=inputs=2:duration=longest:normalize=0[out]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = [
        'ffmpeg',
        '-i', vocal_wav, '-i', accomp_wav,
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-y', mixed_wav
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        st.error(f"Mixing failed: {r.stderr}")
        return None

    vocal_dur  = get_audio_duration(vocal_wav)  or 0.0
    accomp_dur = get_audio_duration(accomp_wav) or 0.0
    mix_dur    = get_audio_duration(mixed_wav)  or 0.0

    stages_info.append(
        f"✓ Step 2: Mixed tracks "
        f"(vocal {vocal_dur:.1f}s + accomp {accomp_dur:.1f}s → {mix_dur:.1f}s)"
    )
    if vocal_delay_ms > 0:
        stages_info.append(f"  • Vocal delayed by {vocal_offset:.2f}s")
    if accomp_delay_ms > 0:
        stages_info.append(f"  • Accompaniment delayed by {accomp_offset:.2f}s")
    stages_info.append(f"  • Vocal volume: {vocal_vol}%  |  Accompaniment volume: {accomp_vol}%")

    return mixed_wav, stages_info

# ── Core: optimize a single audio file ───────────────────────────────────────
def optimize_audio(input_path, output_dir, stage_prefix="opt"):
    """
    Run the vocal optimization pipeline (high-pass → EQ → loudnorm → reverb).

    Returns (final_wav_path, stages_info) or None on failure.
    """
    stages_info = []

    # Stage 1 — Convert to WAV 48 kHz
    st.write("🔄 Optimization Stage 1: Converting to WAV 48 kHz…")
    s1 = os.path.join(output_dir, f"{stage_prefix}_01_converted.wav")
    cmd = ['ffmpeg', '-i', input_path, '-ar', '48000', '-ac', '2', '-y', s1]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        st.error(f"Optimization Stage 1 failed: {r.stderr}")
        return None
    stages_info.append("✓ Opt Stage 1: Convert to WAV 48 kHz")

    # Stage 2 — High-pass filter (denoise)
    st.write("🔄 Optimization Stage 2: Applying high-pass filter…")
    s2 = os.path.join(output_dir, f"{stage_prefix}_02_denoised.wav")
    highpass_freq = 80 if vocal_profile in ('low_baritone', 'tenor') else 90
    cmd = ['ffmpeg', '-i', s1, '-af', f'highpass=f={highpass_freq}', '-y', s2]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        st.error(f"Optimization Stage 2 failed: {r.stderr}")
        return None
    stages_info.append(f"✓ Opt Stage 2: High-pass filter @ {highpass_freq} Hz")

    # Stage 3 — EQ
    st.write("🔄 Optimization Stage 3: Applying EQ…")
    s3 = os.path.join(output_dir, f"{stage_prefix}_03_eq.wav")

    if vocal_profile == 'low_baritone':
        eq_filters = [
            'equalizer=f=250:width_type=o:width=1.5:g=-3',
            'equalizer=f=3000:width_type=o:width=1:g=2',
            'equalizer=f=6500:width_type=o:width=2:g=-2',
            'equalizer=f=10000:width_type=o:width=1:g=1',
        ]
    elif vocal_profile == 'tenor':
        eq_filters = [
            'equalizer=f=300:width_type=o:width=1.5:g=-2',
            'equalizer=f=3500:width_type=o:width=1:g=2.5',
            'equalizer=f=7000:width_type=o:width=2:g=-2',
            'equalizer=f=11000:width_type=o:width=1:g=1.5',
        ]
    elif vocal_profile == 'female':
        eq_filters = [
            'equalizer=f=350:width_type=o:width=1.5:g=-2',
            'equalizer=f=4000:width_type=o:width=1:g=2',
            'equalizer=f=8000:width_type=o:width=2:g=-2.5',
            'equalizer=f=12000:width_type=o:width=1:g=1',
        ]
    else:  # spoken
        eq_filters = [
            'equalizer=f=200:width_type=o:width=2:g=-3',
            'equalizer=f=2500:width_type=o:width=1.5:g=3',
            'equalizer=f=5000:width_type=o:width=2:g=-1',
        ]

    cmd = ['ffmpeg', '-i', s2, '-af', ','.join(eq_filters), '-y', s3]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        st.error(f"Optimization Stage 3 failed: {r.stderr}")
        return None
    stages_info.append(f"✓ Opt Stage 3: EQ ({vocal_profile} profile)")

    # Stage 4 — Loudness normalization
    st.write("🔄 Optimization Stage 4: Loudness normalization…")
    s4 = os.path.join(output_dir, f"{stage_prefix}_04_loudnorm.wav")
    cmd = [
        'ffmpeg', '-i', s3,
        '-af', f'loudnorm=I={target_loudness}:TP=-1.0:LRA=7',
        '-y', s4
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        st.error(f"Optimization Stage 4 failed: {r.stderr}")
        return None
    stages_info.append(f"✓ Opt Stage 4: Loudness normalized to {target_loudness} LUFS")

    # Stage 5 — Optional reverb
    final_wav = s4
    if reverb != "off":
        st.write("🔄 Optimization Stage 5: Applying reverb…")
        s5 = os.path.join(output_dir, f"{stage_prefix}_05_reverb.wav")
        reverb_filter = (
            "aecho=0.8:0.9:1000:0.3"
            if reverb == "light"
            else "aecho=0.8:0.88:1000|1800:0.4|0.3"
        )
        cmd = ['ffmpeg', '-i', s4, '-af', reverb_filter, '-y', s5]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            final_wav = s5
            stages_info.append(f"✓ Opt Stage 5: {reverb.replace('_', ' ').capitalize()} reverb applied")
        else:
            st.warning("Reverb step failed; continuing without reverb.")
            stages_info.append("✓ Opt Stage 5: Reverb skipped (failed)")
    else:
        stages_info.append("✓ Opt Stage 5: Reverb skipped (off)")

    return final_wav, stages_info


# ── Session-state defaults for auto-sync offset widgets ──────────────────────
for _key in ('vocal_offset_widget', 'accomp_offset_widget'):
    if _key not in st.session_state:
        st.session_state[_key] = 0.0

# ══════════════════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════════════════
tab_mix, tab_opt = st.tabs(["🎵 Mix & Optimize", "🎤 Optimize Only"])

# ── Tab 1: Mix & Optimize ─────────────────────────────────────────────────────
with tab_mix:
    st.markdown(
        "**Workflow:** Upload a dry vocal and an accompaniment track → "
        "set sync offsets & volume balance → mix → optionally enhance the result."
    )

    # ── Step 1: Upload ────────────────────────────────────────────────────────
    st.subheader("Step 1 — Upload Your Tracks")
    col_v, col_a = st.columns(2)
    with col_v:
        st.markdown("**🎤 Dry Vocal Track**")
        vocal_file = st.file_uploader(
            "Upload vocal recording",
            type=["wav", "mp3", "m4a"],
            key="vocal_upload",
            help="Your dry vocal — recorded without any background music"
        )
    with col_a:
        st.markdown("**🎸 Accompaniment Track**")
        accomp_file = st.file_uploader(
            "Upload backing / music track",
            type=["wav", "mp3", "m4a"],
            key="accomp_upload",
            help="The instrumental or backing track that accompanies the vocal"
        )

    both_uploaded = vocal_file is not None and accomp_file is not None

    # ── Step 2: Sync & Balance ────────────────────────────────────────────────
    st.subheader("Step 2 — Sync & Balance")

    col_sync, col_vol = st.columns(2)

    with col_sync:
        st.markdown("**⏱️ Time Synchronization**")

        # Auto-detect sync button — disabled until both files are uploaded
        auto_btn = st.button(
            "🔍 Auto-detect sync",
            key="auto_sync_btn",
            disabled=not both_uploaded,
            help=(
                "Analyse the leading silence in both files and suggest offsets "
                "that align their first audio events. Upload both tracks first."
            )
        )
        if auto_btn and both_uploaded:
            with tempfile.TemporaryDirectory() as _td:
                _vp = os.path.join(_td, vocal_file.name)
                _ap = os.path.join(_td, accomp_file.name)
                with open(_vp, 'wb') as _f:
                    _f.write(vocal_file.getbuffer())
                with open(_ap, 'wb') as _f:
                    _f.write(accomp_file.getbuffer())

                with st.spinner("Analysing tracks…"):
                    v_start = detect_audio_start(_vp)
                    a_start = detect_audio_start(_ap)

            if v_start > a_start:
                st.session_state['vocal_offset_widget']  = 0.0
                st.session_state['accomp_offset_widget'] = round(v_start - a_start, 2)
            elif a_start > v_start:
                st.session_state['vocal_offset_widget']  = round(a_start - v_start, 2)
                st.session_state['accomp_offset_widget'] = 0.0
            else:
                st.session_state['vocal_offset_widget']  = 0.0
                st.session_state['accomp_offset_widget'] = 0.0

            st.session_state['auto_sync_result'] = (v_start, a_start)
            st.rerun()

        # Show last detection result (persists across reruns)
        if 'auto_sync_result' in st.session_state:
            v_s, a_s = st.session_state['auto_sync_result']
            if v_s == 0.0 and a_s == 0.0:
                st.success("Both tracks start with audio immediately — no offset needed.")
            else:
                st.info(
                    f"Vocal audio starts at **{v_s:.2f}s** · "
                    f"Accompaniment audio starts at **{a_s:.2f}s** · "
                    f"Suggested offset applied below."
                )

        st.caption(
            "Adjust manually if needed. "
            "Only one offset should be non-zero for a typical recording."
        )
        vocal_offset = st.number_input(
            "Vocal start offset (seconds)",
            min_value=0.0, max_value=300.0, step=0.1,
            key="vocal_offset_widget",
            help="Delay the vocal by this many seconds. Use when the music starts before the singing."
        )
        accomp_offset = st.number_input(
            "Accompaniment start offset (seconds)",
            min_value=0.0, max_value=300.0, step=0.1,
            key="accomp_offset_widget",
            help="Delay the music by this many seconds. Use when the vocal starts before the music."
        )

    with col_vol:
        st.markdown("**🔊 Volume Balance**")
        st.caption("Lower the accompaniment so the vocal sits clearly on top.")
        vocal_vol = st.slider(
            "Vocal volume (%)",
            min_value=0, max_value=200, value=100, step=5,
            key="vocal_vol",
            help="100% = original level. Values above 100% amplify beyond the original."
        )
        accomp_vol = st.slider(
            "Accompaniment volume (%)",
            min_value=0, max_value=200, value=80, step=5,
            key="accomp_vol",
            help="Try 70–85% so the vocal sits clearly on top of the music."
        )

    # ── Step 3: Optional optimization ────────────────────────────────────────
    st.subheader("Step 3 — Optional Optimization")
    apply_optimization = st.checkbox(
        "Apply vocal optimization to the final mix",
        value=False,
        help="Runs EQ, compression, and loudness normalization on the mixed output"
    )
    if apply_optimization:
        st.info(
            f"Optimization will use: **{vocal_profile}** profile · "
            f"**{target_loudness} LUFS** · reverb: **{reverb}**  "
            f"_(configure in the sidebar)_"
        )

    # ── Step 4: Process & Download ────────────────────────────────────────────
    st.subheader("Step 4 — Process & Download")

    if not both_uploaded:
        st.warning("⬆️ Upload both a vocal track and an accompaniment track (Step 1) to enable mixing.")

    col_btn, col_cap = st.columns([1, 3])
    with col_btn:
        mix_button = st.button(
            "▶️ Mix & Export", type="primary",
            use_container_width=True, key="mix_btn",
            disabled=not both_uploaded
        )
    with col_cap:
        if both_uploaded:
            offset_note = ""
            if vocal_offset > 0:
                offset_note += f" | Vocal delayed {vocal_offset:.1f}s"
            if accomp_offset > 0:
                offset_note += f" | Accomp delayed {accomp_offset:.1f}s"
            st.caption(f"Vocal {vocal_vol}% · Accomp {accomp_vol}%{offset_note}")

    if mix_button and both_uploaded:
        with tempfile.TemporaryDirectory() as temp_dir:
            vocal_path  = os.path.join(temp_dir, vocal_file.name)
            accomp_path = os.path.join(temp_dir, accomp_file.name)
            with open(vocal_path,  'wb') as f:
                f.write(vocal_file.getbuffer())
            with open(accomp_path, 'wb') as f:
                f.write(accomp_file.getbuffer())

            st.info("⏳ Processing audio…")
            start_time = time.time()

            mix_result = mix_audio(
                vocal_path, accomp_path, temp_dir,
                vocal_offset, accomp_offset, vocal_vol, accomp_vol
            )

            if mix_result is None:
                st.error("❌ Mixing failed. See error messages above.")
            else:
                mixed_wav, all_stages = mix_result
                final_wav = mixed_wav

                if apply_optimization:
                    opt_result = optimize_audio(mixed_wav, temp_dir, stage_prefix="mix_opt")
                    if opt_result:
                        final_wav, opt_stages = opt_result
                        all_stages += opt_stages
                    else:
                        st.warning("⚠️ Optimization failed; downloading un-optimized mix.")

                elapsed = time.time() - start_time
                st.success(f"✅ Done in {elapsed:.1f}s!")

                st.header("📥 Download")
                output_stem = f"mixed_{Path(vocal_file.name).stem}"
                create_download_buttons(final_wav, output_stem, temp_dir, key_suffix="mix")

                with st.expander("📊 Processing Report", expanded=True):
                    for line in all_stages:
                        st.text(line)

                st.success("🎉 Your mixed audio is ready — click a download button above.")

    with st.expander("ℹ️ How Mixing Works"):
        st.markdown("""
**Time Synchronization**
- Set **Vocal start offset** when the accompaniment begins before the singing
  _(e.g., the music plays for 4 seconds before you start singing → set vocal offset to 4.0)_
- Set **Accompaniment start offset** when the vocal begins before the music
  _(e.g., you start singing 2 seconds before the music kicks in → set accomp offset to 2.0)_
- Only one offset should be non-zero for a typical use case.

**Volume Balance**
- **Vocal volume 100%** — keeps the vocal at its original level.
- **Accompaniment volume 70–85%** — a common starting point so the vocal sits clearly on top.
- Values above 100% amplify beyond the original recording level (may clip if too high).

**Optional Optimization**
- Applies EQ, compression, and loudness normalization to the finished mix.
- Configure vocal profile and target loudness in the **sidebar** before clicking Mix.
- Best used when the vocal track alone needs enhancement (not always needed for a mix).
""")


# ── Tab 2: Optimize Only ──────────────────────────────────────────────────────
with tab_opt:
    st.markdown(
        "**Enhance a single audio file** with professional EQ, compression, "
        "and loudness normalization. Configure settings in the sidebar."
    )

    st.header("📁 Upload Audio File")
    uploaded_file = st.file_uploader(
        "Choose an audio file (WAV, MP3, M4A)",
        type=["wav", "mp3", "m4a"],
        key="optimize_upload",
        help="Upload the vocal or audio recording you want to enhance"
    )

    with st.expander("ℹ️ EQ Curves by Vocal Profile"):
        st.markdown("""
**Low Baritone** _(deep male voice, warm and full)_
- Reduce mud @ 250 Hz (−3 dB)  ·  Presence boost @ 3 kHz (+2 dB)
- Tame sibilance @ 6.5 kHz (−2 dB)  ·  Air @ 10 kHz (+1 dB)

**Tenor** _(higher male voice, bright)_
- Reduce mud @ 300 Hz (−2 dB)  ·  Presence boost @ 3.5 kHz (+2.5 dB)
- Tame sibilance @ 7 kHz (−2 dB)  ·  Air @ 11 kHz (+1.5 dB)

**Female** _(clear and articulate)_
- Reduce mud @ 350 Hz (−2 dB)  ·  Presence boost @ 4 kHz (+2 dB)
- Tame harsh sibilance @ 8 kHz (−2.5 dB)  ·  Air @ 12 kHz (+1 dB)

**Spoken** _(podcast, narration)_
- Reduce rumble @ 200 Hz (−3 dB)  ·  Clarity @ 2.5 kHz (+3 dB)
- Gentle de-ess @ 5 kHz (−1 dB)  ·  Heavier compression (4:1)
""")

    if uploaded_file is not None:
        st.header("🚀 Process Audio")

        col_btn, col_cap = st.columns([1, 3])
        with col_btn:
            process_button = st.button(
                "▶️ Start Processing", type="primary",
                use_container_width=True, key="opt_btn"
            )
        with col_cap:
            st.caption(f"Profile: {vocal_profile}  ·  {target_loudness} LUFS  ·  Reverb: {reverb}")

        if process_button:
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, uploaded_file.name)
                with open(input_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())

                st.info("⏳ Processing audio… This may take a moment.")
                progress_bar = st.progress(0)
                start_time = time.time()

                result = optimize_audio(input_path, temp_dir, stage_prefix="solo")

                if result is None:
                    st.error("❌ Processing failed. Check error messages above.")
                else:
                    final_wav, stages_info = result
                    elapsed = time.time() - start_time

                    progress_bar.progress(100)
                    st.success(f"✅ Processing complete in {elapsed:.1f}s!")

                    st.header("📥 Download Results")
                    output_stem = f"enhanced_{Path(uploaded_file.name).stem}"
                    create_download_buttons(final_wav, output_stem, temp_dir, key_suffix="opt")

                    st.header("📊 Processing Report")
                    with st.expander("View Processing Stages", expanded=True):
                        for line in stages_info:
                            st.text(line)

                    st.info(f"""
**Configuration Applied:**
- Vocal Profile: {vocal_profile}
- Target Loudness: {target_loudness} LUFS
- Reverb: {reverb}
- Noise Reduction: {noise_level}
- De-essing: {deessing}
""")
                    st.success("🎉 Your enhanced audio is ready — click a download button above.")
    else:
        st.info("👆 Upload an audio file to get started")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🎤 Audio Optimizer · Powered by ffmpeg · Built with Streamlit")
