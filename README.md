# 🎤 Audio Optimizer App

A simple web-based audio processing tool for enhancing vocal recordings with professional-quality EQ, compression, and loudness normalization.

## Features

- 🎵 **Vocal Enhancement**: Denoise, EQ, compression, de-essing, and loudness normalization
- 🎛️ **Multiple Vocal Profiles**: Low baritone, tenor, female, and spoken word presets
- 📊 **Target Loudness**: Normalize to streaming standards (-14 LUFS)
- 🎚️ **Optional Reverb**: Add subtle room ambience or pop ballad reverb
- 📁 **Easy File Handling**: Drag-and-drop audio upload, instant download
- 🌐 **Web Interface**: Clean, simple UI accessible in your browser

## Quick Start

### Prerequisites

1. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
2. **ffmpeg** - Install with:
   ```bash
   brew install ffmpeg
   ```

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   streamlit run audio_optimizer_app.py
   ```

3. **Open your browser:**
   - The app will automatically open at `http://localhost:8501`
   - If not, manually navigate to that URL

## Usage

1. **Upload your audio file** (WAV, MP3, or M4A)
2. **Configure settings** in the sidebar:
   - Choose vocal profile (low baritone, tenor, female, spoken)
   - Set target loudness (default: -14 LUFS for streaming)
   - Select reverb amount (off, light, pop ballad)
3. **Click "Start Processing"**
4. **Download results** - Both WAV and MP3 (320kbps) versions

## Vocal Profiles

| Profile | Best For | EQ Characteristics |
|---------|----------|-------------------|
| **Low Baritone** | Deep male voice | -3dB @ 250Hz, +2dB @ 3kHz |
| **Tenor** | Higher male voice | -2dB @ 300Hz, +2.5dB @ 3.5kHz |
| **Female** | Female voice | -2dB @ 350Hz, +2dB @ 4kHz |
| **Spoken** | Podcast, narration | -3dB @ 200Hz, +3dB @ 2.5kHz |

## Target Loudness Standards

- **-14 LUFS**: Spotify, Apple Music, YouTube (default)
- **-16 LUFS**: Podcast standard
- **-23 LUFS**: Broadcast standard (Europe)

## Sharing the App

### Option 1: Share Files
Share these files with others:
- `audio_optimizer_app.py`
- `requirements.txt`
- `README.md`

Recipients just need to follow the Quick Start instructions above.

### Option 2: Deploy to Streamlit Cloud (Free)
1. Create a GitHub repository with these files
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy!

Your app will be available at a public URL like `https://yourapp.streamlit.app`

## What the Processing Does

1. **Convert to WAV 48kHz** - Standardize format
2. **High-pass Filter** - Remove rumble below 80-90Hz
3. **EQ + Compression** - Enhance vocal clarity and presence
4. **Loudness Normalization** - Match streaming standards
5. **Optional Reverb** - Add spatial ambience if desired

## Limitations

- Cannot fix severely clipped/distorted input audio
- Cannot add missing frequencies
- Not equivalent to professional studio mastering
- Processing time depends on file length (typically 10-30 seconds)

## Technical Details

- **Built with**: Streamlit (Python web framework)
- **Audio Processing**: ffmpeg
- **Output Formats**: WAV (lossless) + MP3 (320kbps)

## Troubleshooting

**"ffmpeg is not installed"**
- macOS: `brew install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Linux: `sudo apt install ffmpeg`

**App won't start**
- Make sure Python 3.8+ is installed: `python3 --version`
- Install dependencies: `pip install -r requirements.txt`
- Try: `python3 -m streamlit run audio_optimizer_app.py`

**Processing fails**
- Check that input file is valid audio (play it first)
- Ensure sufficient disk space
- Try a shorter audio file to test

## License

Open source - feel free to modify and share!

---

Built with ❤️ using Streamlit and ffmpeg
