# 🎙️ VocalForge

A browser-based tool that turns your home vocal recording into a polished track:

1. **Extract** the instrumental from any song — upload a full song or paste a URL and the app strips the vocals out.
2. **Mix** your dry vocal with the accompaniment — with auto-sync and volume balance.
3. **Optimize** the result with professional-quality EQ, compression, and loudness normalization.
4. **Download** as lossless WAV and/or 320 kbps MP3.

Built with [Streamlit](https://streamlit.io) and [ffmpeg](https://ffmpeg.org) — no plugins, no subscriptions, runs entirely on your machine.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Feature Guide — Mix & Optimize Tab](#feature-guide--mix--optimize-tab)
3. [Feature Guide — Optimize Only Tab](#feature-guide--optimize-only-tab)
4. [Sidebar Settings Reference](#sidebar-settings-reference)
5. [Tips for Best Results](#tips-for-best-results)
6. [Loudness Standards](#loudness-standards)
7. [Deploying to Streamlit Cloud](#deploying-to-streamlit-cloud)
8. [Troubleshooting](#troubleshooting)
9. [Technical Details](#technical-details)

---

## Quick Start

### Prerequisites

| Requirement | How to install |
|-------------|---------------|
| Python 3.8+ | [python.org](https://www.python.org/downloads/) |
| ffmpeg | macOS: `brew install ffmpeg` · Windows: [ffmpeg.org](https://ffmpeg.org/download.html) · Linux: `sudo apt install ffmpeg` |

### Installation & Launch

```bash
# 1. Clone or download the repository
git clone https://github.com/TonyBY/audio-optimizer.git
cd audio-optimizer

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run audio_optimizer_app.py
```

The app opens automatically at **http://localhost:8501**. If it doesn't, navigate there manually.

> **Windows users:** Run `run_app.bat` instead of step 3.

---

## Feature Guide — Mix & Optimize Tab

This tab guides you through **four steps** to blend a dry vocal with an accompaniment track.

### Step 1 — Upload Your Tracks

| Upload slot | What to put here |
|-------------|-----------------|
| **Dry Vocal Track** | Your vocal recording with no music in the background (recorded at home or in a studio) |
| **Accompaniment Track** | The instrumental / backing track (karaoke version, piano accompaniment, full band, etc.) |

Supported formats: **WAV, MP3, M4A**

Both files must be uploaded before you can proceed.

---

### Step 2 — Sync & Balance

#### Time Synchronization

Most recordings don't start at exactly the same moment. Use these controls to align them:

| Setting | When to use it | Example |
|---------|---------------|---------|
| **Vocal start offset** | The music starts *before* the singing | Music intro plays for 8 seconds → set vocal offset to `8.0` |
| **Accompaniment start offset** | The vocal starts *before* the music | You start humming 2 seconds before the beat drops → set accomp offset to `2.0` |

> **Tip:** Only one offset should be non-zero for a typical recording. If both are zero, the two tracks start simultaneously.

**How to find the right offset:**
1. Listen to both files separately and note where the singing actually begins (e.g., 0:08 on the vocal file) and where the music track expects the vocal to start (e.g., 0:00 on the backing track).
2. The difference is your offset. In the example above, set **Accompaniment start offset = 8.0** (delay the music by 8 s so the vocal and music land together).

#### Volume Balance

| Setting | Default | Guidance |
|---------|---------|---------|
| **Vocal volume (%)** | 100% | Keep at 100% unless the vocal is too loud relative to the music |
| **Accompaniment volume (%)** | 80% | Start around 70–85%; lower it until the vocal sits comfortably on top |

Values above 100% amplify beyond the original level — be careful with clipping at very high values.

---

### Step 3 — Optional Optimization

Check **"Apply vocal optimization to the final mix"** to run the enhancement pipeline (EQ → loudness normalization → reverb) on the mixed output.

Configure the optimization parameters in the **sidebar** *before* clicking the process button:

- **Vocal Profile** — choose the EQ preset that matches the voice type.
- **Target Loudness** — set the LUFS target for streaming or broadcast.
- **Reverb** — add subtle space or a pop ballad reverb.

> You do not need optimization if the vocal was already professionally recorded. It is most useful when you recorded at home and want to polish the final mix.

---

### Step 4 — Process & Download

Click **▶️ Mix & Export**. The app will:

1. Convert both tracks to 48 kHz stereo WAV.
2. Apply your time offsets and volume levels.
3. Mix the two streams together (longer track determines output length).
4. _(If enabled)_ Run the optimization pipeline.
5. Offer **WAV** (lossless) and **MP3** (320 kbps) downloads.

A processing report shows every stage that was applied.

---

## Feature Guide — Optimize Only Tab

Use this tab to enhance a **single** audio file — a standalone vocal, a finished mix, a podcast recording, etc.

### Steps

1. **Upload** one audio file (WAV, MP3, or M4A).
2. **Configure** settings in the sidebar (vocal profile, loudness, reverb).
3. Click **▶️ Start Processing**.
4. **Download** the enhanced file in WAV and/or MP3 format.

### What the Pipeline Does

| Stage | What happens |
|-------|-------------|
| **1. Convert** | Standardizes to 48 kHz stereo WAV |
| **2. High-pass filter** | Removes low-frequency rumble below 80–90 Hz |
| **3. EQ** | Applies the vocal profile's parametric EQ curve |
| **4. Loudness normalization** | Normalizes to the target LUFS (e.g., −14 LUFS for streaming) |
| **5. Reverb** _(optional)_ | Adds light or pop-ballad reverb if selected |

---

## Sidebar Settings Reference

All settings in the sidebar apply to **both** tabs whenever optimization is used.

| Setting | Options | Description |
|---------|---------|-------------|
| **Vocal Profile** | `low_baritone` `tenor` `female` `spoken` | Selects the parametric EQ curve optimized for that voice type |
| **Target Loudness** | −23 to −9 LUFS | Streaming standard is −14 LUFS; podcast standard is −16 LUFS |
| **Reverb** | `off` `light` `pop_ballad` | Adds spatial ambience after loudness normalization |
| **Noise Reduction** | `light` `medium` `strong` | Displayed in the report; informs the high-pass filter cutoff |
| **De-essing** | `light` `medium` `strong` | Displayed in the report; the EQ curve handles sibilance reduction |
| **Export MP3** | ✓ / ✗ | When checked, produces a 320 kbps MP3 alongside the WAV |

### Vocal Profile EQ Details

| Profile | Best for | EQ bands |
|---------|----------|----------|
| **Low Baritone** | Deep male voice | −3 dB @ 250 Hz, +2 dB @ 3 kHz, −2 dB @ 6.5 kHz, +1 dB @ 10 kHz |
| **Tenor** | Higher male voice | −2 dB @ 300 Hz, +2.5 dB @ 3.5 kHz, −2 dB @ 7 kHz, +1.5 dB @ 11 kHz |
| **Female** | Female voice | −2 dB @ 350 Hz, +2 dB @ 4 kHz, −2.5 dB @ 8 kHz, +1 dB @ 12 kHz |
| **Spoken** | Podcast, narration | −3 dB @ 200 Hz, +3 dB @ 2.5 kHz, −1 dB @ 5 kHz |

---

## Tips for Best Results

### Recording your vocal

- Record in a quiet room — the app cannot remove reverb that is already in the recording.
- Use a pop filter to reduce plosives (harsh "p" and "b" sounds).
- Record at a healthy level — peaks around −6 dBFS. Do not clip.

### Choosing the accompaniment

- Use a karaoke / instrumental version of the song, not the full commercial track.
- Make sure both tracks are the same tempo (BPM). The app does **not** time-stretch.

### Sync workflow (recommended)

1. Open both files in a free audio player (e.g., VLC or Audacity) to find the exact start times.
2. Note the timestamp where the vocal phrase begins and where it should fall in the backing track.
3. Enter the difference as the appropriate offset in the app.

### Volume balance

- Start with **Vocal 100% / Accompaniment 80%** and adjust by ear after downloading.
- If the vocal still gets buried, lower the accompaniment further (e.g., 65–70%).
- If the mix sounds thin, raise the accompaniment.

### Optimization

- Enable optimization mainly when the vocal was recorded at home without professional processing.
- For a voice recorded in a studio, optimization may be unnecessary or even counterproductive.
- Match the **Vocal Profile** carefully — using "low_baritone" on a female voice will boost the wrong frequencies.

---

## Loudness Standards

| Platform | Target |
|----------|--------|
| Spotify, Apple Music, YouTube | −14 LUFS |
| Tidal | −14 LUFS |
| Podcast (typical) | −16 LUFS |
| Broadcast (EU) | −23 LUFS |
| CD mastering | −9 to −12 LUFS |

---

## Deploying to Streamlit Cloud

You can host the app for free so anyone can use it via a browser link.

1. Fork or push the repository to your own GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository and `audio_optimizer_app.py`.
4. Click **Deploy** — the app will be live at `https://<your-app>.streamlit.app`.

Streamlit Cloud uses `packages.txt` to install system packages (ffmpeg) automatically.

---

## Troubleshooting

### "ffmpeg is not installed"

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

### App won't start

```bash
# Verify Python version (3.8+ required)
python3 --version

# Re-install dependencies
pip install -r requirements.txt

# Alternative launch command
python3 -m streamlit run audio_optimizer_app.py
```

### Processing fails mid-way

- Make sure the uploaded file plays correctly in a media player before uploading.
- Ensure there is sufficient free disk space (the app writes temporary files during processing).
- Try a shorter test clip (30 seconds) to isolate whether the issue is file-specific.

### Mixing output is out of sync

- Re-check the timestamps: open both files in Audacity, find the exact frame where the vocal begins and where the accompaniment expects it, then compute the offset precisely.
- Only one of the two offset fields should be non-zero.

### The vocal is too quiet / too loud in the mix

- Adjust the volume sliders in Step 2 and re-run.
- If the vocal is consistently too quiet, try raising **Vocal volume** to 120–150%.
- If the backing track overwhelms the vocal, lower **Accompaniment volume** to 60–70%.

### Optimization makes the audio sound worse

- Try a different **Vocal Profile** that better matches the voice type.
- Reduce the **Target Loudness** (e.g., −16 LUFS) for a more natural result.
- Turn **Reverb** off; the reverb filter is intentionally noticeable.

---

## Technical Details

| Item | Detail |
|------|--------|
| Framework | [Streamlit](https://streamlit.io) ≥ 1.30 |
| Audio engine | [ffmpeg](https://ffmpeg.org) (system package) |
| Mixing filter | `amix` with `normalize=0` + `adelay` + `volume` |
| Normalization | `loudnorm` (EBU R128) |
| Output formats | WAV (lossless PCM) · MP3 (320 kbps CBR) |
| Temporary files | Written to a system temp directory, deleted after download |
| Supported input | WAV, MP3, M4A (any sample rate; converted to 48 kHz internally) |

---

## Limitations

- Cannot fix severely clipped or distorted input audio.
- Cannot add frequencies that were never captured.
- Does **not** perform pitch correction or time-stretching — both tracks must already be at the same tempo and pitch.
- Not a replacement for professional mastering.
- Processing time scales with file length (typically 15–60 seconds for a 3–5 minute song).

---

## License

Open source — feel free to modify and share!

---

Built with ❤️ using Streamlit and ffmpeg · **VocalForge**
