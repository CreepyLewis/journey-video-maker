# 🎬 Journey Video Maker

> Auto-generate TikTok/Reels-style journey videos from images + a JSON story file.
> No Premiere Pro, no CapCut — just Python.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![MoviePy](https://img.shields.io/badge/MoviePy-1.0.3-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/journey-video-maker.git
cd journey-video-maker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate a DEMO video (no images needed)
python src/make_video.py --demo

# Output: output/demo_journey.mp4
```

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **9:16 vertical format** | Perfect for TikTok, Instagram Reels, YouTube Shorts |
| **Ken Burns effect** | Subtle zoom on each image slide |
| **Animated title cards** | Glowing intro with grid overlay |
| **Location tags** | Pill-shaped GPS tags on each slide |
| **Stats card** | Final summary slide with your trip data |
| **4 themes** | `neon` · `warm` · `dark` · `fire` |
| **Background music** | Drop an MP3 in `assets/music/` |
| **Watermark** | Auto-adds your handle to every frame |
| **JSON-driven** | Define your whole story in one file |

---

## 📁 Project Structure

```
journey-video-maker/
├── src/
│   └── make_video.py        # Main script
├── assets/
│   ├── images/              # Put your photos here
│   └── music/               # Optional background music (.mp3 / .wav)
├── output/                  # Generated videos appear here
├── story_example.json       # Example story definition
├── requirements.txt
└── README.md
```

---

## 📝 Create Your Story

Copy `story_example.json` and edit it:

```json
{
  "title": "MY MOTO JOURNEY",
  "subtitle": "2,000 KM ACROSS EAST AFRICA",
  "settings": {
    "theme": "neon",
    "watermark": "@YourHandle",
    "audio": "assets/music/background.mp3"
  },
  "slides": [
    {
      "image":    "assets/images/day1.jpg",
      "caption":  "Day 1 – Left Nairobi at sunrise 🌅",
      "location": "Nairobi, Kenya"
    }
  ],
  "stats": {
    "Total Distance": "2,048 km",
    "Days":           "5"
  }
}
```

Then run:
```bash
python src/make_video.py --story my_story.json
```

---

## 🎨 Themes

```bash
python src/make_video.py --demo --theme neon   # Green/cyan on black (default)
python src/make_video.py --demo --theme warm   # Orange/red warm tones
python src/make_video.py --demo --theme dark   # White on pure black
python src/make_video.py --demo --theme fire   # Orange/yellow flames
```

---

## ⚙️ CLI Options

```
python src/make_video.py [OPTIONS]

  --story  -s    Path to story JSON file    (default: story.json)
  --demo   -d    Generate a demo video
  --theme  -t    Color theme: neon|warm|dark|fire  (default: neon)
  --out    -o    Output filename            (default: auto timestamp)
```

---

## 🛠️ Requirements

- Python 3.8+
- FFmpeg (required by MoviePy)

**Install FFmpeg:**
```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

---

## 🌐 Deploy / Share

### GitHub Actions auto-render
```yaml
# .github/workflows/render.yml
on: [push]
jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: sudo apt install -y ffmpeg
      - run: pip install -r requirements.txt
      - run: python src/make_video.py --story story.json
      - uses: actions/upload-artifact@v3
        with:
          name: video
          path: output/*.mp4
```

---

## 📦 GitHub Setup

```bash
git init
git add .
git commit -m "🎬 Initial commit — Journey Video Maker"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/journey-video-maker.git
git push -u origin main
```

---

## 📄 License
MIT — free to use and modify.
