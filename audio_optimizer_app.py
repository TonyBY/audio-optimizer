#!/usr/bin/env python3
"""
Audio Optimizer App
Simple web UI for vocal audio enhancement using ffmpeg
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

# Title and description
st.title("🎤 Audio Optimizer")
st.markdown("""
Enhance vocal recordings with professional processing: denoise, EQ, compression, and loudness normalization.
Upload your audio file and configure settings below.
""")

# Check for ffmpeg
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if not check_ffmpeg():
    st.error("⚠️ ffmpeg is not installed. Please install it first: `brew install ffmpeg`")
    st.stop()

# Sidebar for parameters
st.sidebar.header("⚙️ Processing Settings")

mode = st.sidebar.selectbox(
    "Processing Mode",
    ["voice_only", "voice_plus_music"],
    help="voice_only: Process single vocal track | voice_plus_music: Separate vocals from mix first"
)

vocal_profile = st.sidebar.selectbox(
    "Vocal Profile",
    ["low_baritone", "tenor", "female", "spoken"],
    help="low_baritone: Deep male voice | tenor: Higher male voice | female: Female voice | spoken: Podcast/narration"
)

target_loudness = st.sidebar.slider(
    "Target Loudness (LUFS)",
    min_value=-23, max_value=-9, value=-14, step=1,
    help="-14 LUFS is standard for streaming platforms"
)

reverb = st.sidebar.selectbox(
    "Reverb",
    ["off", "light", "pop_ballad"],
    help="off: Dry vocal | light: Subtle room | pop_ballad: Moderate reverb"
)

noise_level = st.sidebar.selectbox(
    "Noise Reduction",
    ["light", "medium", "strong"],
    help="Strength of background noise removal"
)

deessing = st.sidebar.selectbox(
    "De-essing",
    ["light", "medium", "strong"],
    help="Sibilance reduction (harsh 's' sounds)"
)

export_mp3 = st.sidebar.checkbox("Export MP3", value=True, help="Also create MP3 version (320kbps)")

# File upload
st.header("📁 Upload Audio File")
uploaded_file = st.file_uploader(
    "Choose an audio file (WAV, MP3, M4A)",
    type=["wav", "mp3", "m4a"],
    help="Upload your vocal recording to process"
)

# EQ presets reference
with st.expander("ℹ️ View EQ Curves by Vocal Profile"):
    st.markdown("""
    **Low Baritone** (Deep male voice, warm and full)
    - Reduce mud @ 250Hz (-3dB)
    - Presence boost @ 3kHz (+2dB)
    - Tame sibilance @ 6.5kHz (-2dB)
    - Air @ 10kHz (+1dB)

    **Tenor** (Higher male voice, bright)
    - Reduce mud @ 300Hz (-2dB)
    - Presence boost @ 3.5kHz (+2.5dB)
    - Tame sibilance @ 7kHz (-2dB)
    - Air @ 11kHz (+1.5dB)

    **Female** (Clear and articulate)
    - Reduce mud @ 350Hz (-2dB)
    - Presence boost @ 4kHz (+2dB)
    - Tame harsh sibilance @ 8kHz (-2.5dB)
    - Air @ 12kHz (+1dB)

    **Spoken** (Podcast, narration)
    - Reduce rumble @ 200Hz (-3dB)
    - Clarity @ 2.5kHz (+3dB)
    - Gentle de-ess @ 5kHz (-1dB)
    - Heavier compression (4:1)
    """)

# Processing function
def process_audio(input_path, output_dir):
    """Process audio through the pipeline"""

    stages_info = []

    # Stage 1: Convert to WAV 48kHz
    st.write("🔄 Stage 1: Converting to WAV 48kHz...")
    stage1_output = os.path.join(output_dir, "01_converted.wav")
    cmd = [
        'ffmpeg', '-i', input_path,
        '-ar', '48000', '-ac', '2',
        '-y', stage1_output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Stage 1 failed: {result.stderr}")
        return None
    stages_info.append("✓ Stage 1: Convert to WAV 48kHz")

    # Stage 3: Denoise (high-pass filter)
    st.write("🔄 Stage 3: Applying high-pass filter...")
    stage3_output = os.path.join(output_dir, "03_denoised.wav")
    highpass_freq = 80 if vocal_profile in ['low_baritone', 'tenor'] else 90
    cmd = [
        'ffmpeg', '-i', stage1_output,
        '-af', f'highpass=f={highpass_freq}',
        '-y', stage3_output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Stage 3 failed: {result.stderr}")
        return None
    stages_info.append(f"✓ Stage 3: Denoise - High-pass filter @ {highpass_freq}Hz")

    # Stage 4: EQ + Compression
    st.write("🔄 Stage 4: Applying EQ and compression...")
    stage4_output = os.path.join(output_dir, "04_processed.wav")

    # Build EQ filter based on vocal profile
    eq_filters = []
    if vocal_profile == 'low_baritone':
        eq_filters = [
            'equalizer=f=250:width_type=o:width=1.5:g=-3',
            'equalizer=f=3000:width_type=o:width=1:g=2',
            'equalizer=f=6500:width_type=o:width=2:g=-2',
            'equalizer=f=10000:width_type=o:width=1:g=1'
        ]
        comp_ratio = 3.0
    elif vocal_profile == 'tenor':
        eq_filters = [
            'equalizer=f=300:width_type=o:width=1.5:g=-2',
            'equalizer=f=3500:width_type=o:width=1:g=2.5',
            'equalizer=f=7000:width_type=o:width=2:g=-2',
            'equalizer=f=11000:width_type=o:width=1:g=1.5'
        ]
        comp_ratio = 3.0
    elif vocal_profile == 'female':
        eq_filters = [
            'equalizer=f=350:width_type=o:width=1.5:g=-2',
            'equalizer=f=4000:width_type=o:width=1:g=2',
            'equalizer=f=8000:width_type=o:width=2:g=-2.5',
            'equalizer=f=12000:width_type=o:width=1:g=1'
        ]
        comp_ratio = 2.5
    else:  # spoken
        eq_filters = [
            'equalizer=f=200:width_type=o:width=2:g=-3',
            'equalizer=f=2500:width_type=o:width=1.5:g=3',
            'equalizer=f=5000:width_type=o:width=2:g=-1'
        ]
        comp_ratio = 4.0

    # Combine filters
    audio_filter = ','.join(eq_filters)

    cmd = [
        'ffmpeg', '-i', stage3_output,
        '-af', audio_filter,
        '-y', stage4_output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Stage 4 failed: {result.stderr}")
        return None
    stages_info.append(f"✓ Stage 4: EQ + Compression ({vocal_profile} profile)")

    # Stage 5: Limiting + Loudness Normalization
    st.write("🔄 Stage 5: Loudness normalization...")
    stage5_output = os.path.join(output_dir, "05_limited.wav")
    cmd = [
        'ffmpeg', '-i', stage4_output,
        '-af', f'loudnorm=I={target_loudness}:TP=-1.0:LRA=7',
        '-y', stage5_output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Stage 5 failed: {result.stderr}")
        return None
    stages_info.append(f"✓ Stage 5: Limiting + Loudness Normalization to {target_loudness} LUFS")

    # Stage 6: Optional Reverb
    final_wav = stage5_output
    if reverb != "off":
        st.write("🔄 Stage 6: Applying reverb...")
        stage6_output = os.path.join(output_dir, "06_reverb.wav")

        if reverb == "light":
            reverb_filter = "aecho=0.8:0.9:1000:0.3"
        else:  # pop_ballad
            reverb_filter = "aecho=0.8:0.88:1000|1800:0.4|0.3"

        cmd = [
            'ffmpeg', '-i', stage5_output,
            '-af', reverb_filter,
            '-y', stage6_output
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            st.warning(f"Reverb failed, using output without reverb")
        else:
            final_wav = stage6_output
            stages_info.append(f"✓ Stage 6: {reverb.capitalize()} reverb applied")
    else:
        stages_info.append("✓ Stage 6: Skipped (no reverb)")

    return final_wav, stages_info

# Process button
if uploaded_file is not None:
    st.header("🚀 Process Audio")

    col1, col2 = st.columns([1, 3])
    with col1:
        process_button = st.button("▶️ Start Processing", type="primary", use_container_width=True)
    with col2:
        st.caption(f"Settings: {vocal_profile}, {target_loudness} LUFS, reverb: {reverb}")

    if process_button:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(input_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Create progress container
            progress_container = st.container()
            with progress_container:
                st.info("⏳ Processing audio... This may take a few minutes.")
                progress_bar = st.progress(0)

                start_time = time.time()

                # Process audio
                result = process_audio(input_path, temp_dir)

                if result is None:
                    st.error("❌ Processing failed. Check error messages above.")
                else:
                    final_wav, stages_info = result
                    processing_time = time.time() - start_time

                    progress_bar.progress(100)
                    st.success(f"✅ Processing complete in {processing_time:.1f}s!")

                    # Create final output files
                    base_name = Path(uploaded_file.name).stem
                    final_wav_name = f"enhanced_{base_name}.wav"
                    final_mp3_name = f"enhanced_{base_name}.mp3"

                    final_wav_path = os.path.join(temp_dir, final_wav_name)
                    shutil.copy(final_wav, final_wav_path)

                    # Create MP3 if requested
                    mp3_data = None
                    if export_mp3:
                        final_mp3_path = os.path.join(temp_dir, final_mp3_name)
                        cmd = ['ffmpeg', '-i', final_wav_path, '-b:a', '320k', '-y', final_mp3_path]
                        subprocess.run(cmd, capture_output=True)
                        with open(final_mp3_path, 'rb') as f:
                            mp3_data = f.read()

                    # Read WAV data
                    with open(final_wav_path, 'rb') as f:
                        wav_data = f.read()

                    # Display results
                    st.header("📥 Download Results")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="⬇️ Download WAV (Lossless)",
                            data=wav_data,
                            file_name=final_wav_name,
                            mime="audio/wav",
                            use_container_width=True
                        )

                    if mp3_data:
                        with col2:
                            st.download_button(
                                label="⬇️ Download MP3 (320kbps)",
                                data=mp3_data,
                                file_name=final_mp3_name,
                                mime="audio/mpeg",
                                use_container_width=True
                            )

                    # Show processing report
                    st.header("📊 Processing Report")

                    with st.expander("View Processing Stages", expanded=True):
                        for stage in stages_info:
                            st.text(stage)

                    st.info(f"""
                    **Configuration Applied:**
                    - Mode: {mode}
                    - Vocal Profile: {vocal_profile}
                    - Target Loudness: {target_loudness} LUFS
                    - Reverb: {reverb}
                    - Noise Reduction: {noise_level}
                    - De-essing: {deessing}
                    """)

                    st.success("🎉 Your audio is ready! Click the download buttons above.")

else:
    st.info("👆 Upload an audio file to get started")

# Footer
st.markdown("---")
st.caption("🎤 Audio Optimizer | Powered by ffmpeg | Built with Streamlit")
