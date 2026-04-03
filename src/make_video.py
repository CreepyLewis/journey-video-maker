"""
╔══════════════════════════════════════════════════════╗
║        JOURNEY VIDEO MAKER                          ║
║   Auto-generate TikTok/Reels-style journey videos   ║
║   Requires: pip install moviepy pillow numpy        ║
╚══════════════════════════════════════════════════════╝
"""

import os, sys, json, math, random, textwrap
from pathlib import Path
from datetime import datetime

try:
    from moviepy.editor import (
        VideoFileClip, ImageClip, AudioFileClip, TextClip,
        CompositeVideoClip, concatenate_videoclips, ColorClip,
        VideoClip
    )
    from moviepy.video.fx.all import fadein, fadeout, crop
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    print("\n❌  Missing dependencies. Run:\n")
    print("    pip install moviepy pillow numpy\n")
    sys.exit(1)

# ── Config ──────────────────────────────────────────
CONFIG = {
    "width":      1080,
    "height":     1920,   # 9:16 vertical (TikTok/Reels)
    "fps":        30,
    "duration_per_slide": 3.5,  # seconds per image if no video
    "output_dir": "output",
    "font_size":  72,
    "watermark":  "@JourneyMaker",
}

PALETTE = {
    "neon":   {"bg": (5, 5, 15),    "title": (57, 255, 20), "sub": (0, 207, 255), "text": (230, 238, 210)},
    "warm":   {"bg": (20, 10, 5),   "title": (255, 180, 0), "sub": (255, 80, 40),  "text": (255, 240, 220)},
    "dark":   {"bg": (10, 10, 10),  "title": (255, 255, 255),"sub": (150,150,150), "text": (200, 200, 200)},
    "fire":   {"bg": (10, 0, 0),    "title": (255, 80, 0),   "sub": (255, 200, 0), "text": (255, 230, 200)},
}

# ── Frame-by-frame PIL rendering ─────────────────────
class FrameRenderer:
    def __init__(self, w, h, theme="neon"):
        self.w = w
        self.h = h
        self.colors = PALETTE.get(theme, PALETTE["neon"])
        self._load_fonts()

    def _load_fonts(self):
        """Try system fonts, fall back to default."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        loaded = None
        for p in font_paths:
            if os.path.exists(p):
                try:
                    loaded = p
                    break
                except: pass

        try:
            self.font_xl   = ImageFont.truetype(loaded, 90)  if loaded else ImageFont.load_default()
            self.font_lg   = ImageFont.truetype(loaded, 60)  if loaded else ImageFont.load_default()
            self.font_md   = ImageFont.truetype(loaded, 40)  if loaded else ImageFont.load_default()
            self.font_sm   = ImageFont.truetype(loaded, 28)  if loaded else ImageFont.load_default()
            self.font_xs   = ImageFont.truetype(loaded, 22)  if loaded else ImageFont.load_default()
        except:
            self.font_xl = self.font_lg = self.font_md = self.font_sm = self.font_xs = ImageFont.load_default()

    # ── Backgrounds ──────────────────────────────────
    def make_gradient_bg(self, color1=None, color2=None):
        """Vertical gradient background."""
        c1 = color1 or self.colors["bg"]
        c2 = color2 or tuple(min(255, x + 30) for x in c1)
        img = Image.new("RGB", (self.w, self.h))
        draw = ImageDraw.Draw(img)
        for y in range(self.h):
            t = y / self.h
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            draw.line([(0, y), (self.w, y)], fill=(r, g, b))
        return img

    def add_grid_overlay(self, img, alpha=20):
        """Add subtle grid lines."""
        overlay = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        color = (*self.colors["title"][:3], alpha)
        for x in range(0, self.w, 60):
            draw.line([(x, 0), (x, self.h)], fill=color, width=1)
        for y in range(0, self.h, 60):
            draw.line([(0, y), (self.w, y)], fill=color, width=1)
        return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    def add_vignette(self, img, strength=0.6):
        """Darken edges."""
        vig = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(vig)
        for i in range(200):
            t = i / 200
            alpha = int(strength * 255 * (t ** 2))
            draw.ellipse(
                [i * self.w / 400, i * self.h / 400,
                 self.w - i * self.w / 400, self.h - i * self.h / 400],
                outline=(0, 0, 0, alpha)
            )
        return Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

    # ── Text helpers ─────────────────────────────────
    def draw_centered_text(self, draw, text, y, font, color, shadow=True, max_width=None):
        """Draw centered text with optional shadow."""
        if max_width:
            # Word wrap
            words = text.split()
            lines, line = [], ""
            for word in words:
                test = line + " " + word if line else word
                bbox = font.getbbox(test)
                if bbox[2] - bbox[0] > max_width and line:
                    lines.append(line)
                    line = word
                else:
                    line = test
            if line: lines.append(line)
            for i, l in enumerate(lines):
                self.draw_centered_text(draw, l, y + i * (font.size + 8), font, color, shadow)
            return y + len(lines) * (font.size + 8)
        
        bbox = draw._image.size
        try:
            w = font.getlength(text)
        except:
            w = len(text) * (font.size * 0.6)
        x = (self.w - w) / 2
        if shadow:
            draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), text, font=font, fill=color)
        return y + font.size + 12

    def draw_tag(self, draw, text, x, y, bg_color=None, text_color=None):
        """Pill-shaped tag."""
        bg  = bg_color   or self.colors["title"]
        fg  = text_color or (0, 0, 0)
        bbox = self.font_sm.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = 14
        draw.rounded_rectangle([x, y, x + tw + pad * 2, y + th + pad], radius=8, fill=bg)
        draw.text((x + pad, y + pad // 2), text, font=self.font_sm, fill=fg)

    # ── Slide generators ─────────────────────────────

    def make_intro_slide(self, title, subtitle="", show_frame=0, total_frames=None):
        """Title card / intro slide."""
        total = total_frames or int(CONFIG["duration_per_slide"] * CONFIG["fps"])
        t     = show_frame / max(total, 1)

        img  = self.make_gradient_bg()
        img  = self.add_grid_overlay(img)
        img  = self.add_vignette(img)

        # Animated scan line
        scan_y = int(t * self.h)
        draw_o = ImageDraw.Draw(img.convert("RGBA"))

        draw = ImageDraw.Draw(img)

        # Decorative lines
        c = self.colors["title"]
        line_alpha = min(1.0, t * 3)
        la = int(line_alpha * 180)
        draw.line([(80, self.h // 2 - 100), (self.w - 80, self.h // 2 - 100)],
                  fill=(*c, la), width=2)
        draw.line([(80, self.h // 2 + 140), (self.w - 80, self.h // 2 + 140)],
                  fill=(*c, la), width=2)

        # Title (fade in)
        title_alpha = int(min(1.0, t * 4) * 255)
        y = self.h // 2 - 80
        self.draw_centered_text(draw, title.upper(), y, self.font_xl,
                                (*self.colors["title"][:3],), max_width=self.w - 120)

        if subtitle:
            y2 = self.h // 2 + 60
            self.draw_centered_text(draw, subtitle, y2, self.font_md,
                                    self.colors["sub"])

        # Watermark
        draw.text((self.w - 200, self.h - 60), CONFIG["watermark"],
                  font=self.font_xs, fill=(*self.colors["text"][:3], 120))

        return img

    def make_content_slide(self, image_path=None, caption="", location="",
                           step_num=None, show_frame=0, total_frames=None):
        """A slide with optional background image, caption, and location tag."""
        total = total_frames or int(CONFIG["duration_per_slide"] * CONFIG["fps"])
        t     = show_frame / max(total, 1)

        if image_path and os.path.exists(image_path):
            # Load and fit image
            bg = Image.open(image_path).convert("RGB")
            bg = self._fit_image(bg)
            # Slight zoom effect (Ken Burns)
            zoom  = 1 + t * 0.04
            nw, nh = int(self.w * zoom), int(self.h * zoom)
            bg = bg.resize((nw, nh), Image.LANCZOS)
            ox = (nw - self.w) // 2
            oy = (nh - self.h) // 2
            bg = bg.crop((ox, oy, ox + self.w, oy + self.h))
            # Enhance
            bg = ImageEnhance.Brightness(bg).enhance(0.75)
            bg = ImageEnhance.Contrast(bg).enhance(1.1)
        else:
            bg = self.make_gradient_bg()

        bg = self.add_vignette(bg, strength=0.65)
        draw = ImageDraw.Draw(bg)

        # Caption box at bottom
        if caption:
            box_h = 220
            box_y = self.h - box_h - 40

            # Semi-transparent overlay
            overlay = Image.new("RGBA", (self.w, box_h + 40), (0, 0, 0, 180))
            bg = Image.alpha_composite(bg.convert("RGBA"), overlay.transform(
                (self.w, self.h),
                Image.AFFINE,
                (1, 0, 0, 0, 1, -(self.h - box_h - 40))
            )).convert("RGB")

            draw = ImageDraw.Draw(bg)
            lines = textwrap.wrap(caption, width=24)
            y     = box_y + 20
            for line in lines:
                try:
                    w = self.font_lg.getlength(line)
                except:
                    w = len(line) * 36
                x = (self.w - w) / 2
                draw.text((x + 2, y + 2), line, font=self.font_lg, fill=(0, 0, 0, 200))
                draw.text((x, y), line, font=self.font_lg, fill=self.colors["text"])
                y += self.font_lg.size + 8

        # Location tag
        if location:
            self.draw_tag(draw, "📍 " + location, 40, 60,
                          bg_color=self.colors["title"][:3], text_color=(0, 0, 0))

        # Step counter
        if step_num is not None:
            self.draw_tag(draw, f"#{step_num}", self.w - 120, 60,
                          bg_color=self.colors["sub"][:3], text_color=(0, 0, 0))

        # Watermark
        draw.text((self.w - 200, self.h - 50), CONFIG["watermark"],
                  font=self.font_xs, fill=(*self.colors["text"][:3], 100))

        return bg

    def make_stats_slide(self, stats: dict, title="JOURNEY STATS"):
        """Final stats card."""
        img  = self.make_gradient_bg()
        img  = self.add_grid_overlay(img)
        img  = self.add_vignette(img)
        draw = ImageDraw.Draw(img)

        # Title
        y = 200
        self.draw_centered_text(draw, title, y, self.font_lg, self.colors["title"])
        y += 100

        # Divider
        draw.line([(120, y), (self.w - 120, y)], fill=self.colors["sub"], width=2)
        y += 40

        # Stats rows
        for key, val in stats.items():
            try: kw = self.font_md.getlength(key)
            except: kw = len(key) * 24
            try: vw = self.font_md.getlength(str(val))
            except: vw = len(str(val)) * 24

            draw.text((120, y), key, font=self.font_md, fill=self.colors["sub"])
            draw.text((self.w - 120 - vw, y), str(val), font=self.font_md,
                      fill=self.colors["title"])
            draw.line([(120, y + 50), (self.w - 120, y + 50)],
                      fill=(*self.colors["text"][:3], 30), width=1)
            y += 70

        # Handle
        self.draw_centered_text(draw, CONFIG["watermark"], self.h - 150,
                                self.font_md, self.colors["sub"])
        return img

    def _fit_image(self, img):
        """Cover-fit image to canvas."""
        w, h = img.size
        scale = max(self.w / w, self.h / h)
        nw, nh = int(w * scale), int(h * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        x = (nw - self.w) // 2
        y = (nh - self.h) // 2
        return img.crop((x, y, x + self.w, y + self.h))


# ── Video builder ─────────────────────────────────────
class JourneyVideoMaker:
    def __init__(self, config_path=None):
        self.config    = CONFIG.copy()
        self.renderer  = FrameRenderer(self.config["width"], self.config["height"])
        self.clips     = []
        self.story     = None

        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
                self.config.update(data.get("settings", {}))
                self.story = data

    def build_clip_from_pil(self, get_frame_fn, duration, fps=None):
        """Build a MoviePy clip from a PIL-frame function."""
        fps = fps or self.config["fps"]
        total = int(duration * fps)

        def make_frame(t):
            frame_n = int(t * fps)
            pil_img = get_frame_fn(frame_n, total)
            return np.array(pil_img)

        return VideoClip(make_frame, duration=duration).set_fps(fps)

    def add_intro(self, title, subtitle="", duration=None):
        dur = duration or self.config["duration_per_slide"]
        renderer = self.renderer

        def get_frame(n, total):
            return renderer.make_intro_slide(title, subtitle, n, total)

        clip = self.build_clip_from_pil(get_frame, dur)
        clip = fadein(clip, 0.5)
        self.clips.append(clip)

    def add_content_slide(self, image_path=None, caption="", location="",
                          step_num=None, duration=None):
        dur = duration or self.config["duration_per_slide"]
        renderer = self.renderer

        def get_frame(n, total):
            return renderer.make_content_slide(image_path, caption, location, step_num, n, total)

        clip = self.build_clip_from_pil(get_frame, dur)
        self.clips.append(clip)

    def add_stats(self, stats: dict, title="JOURNEY STATS", duration=4.0):
        renderer = self.renderer
        img = renderer.make_stats_slide(stats, title)
        arr = np.array(img)

        def make_frame(t):
            return arr

        clip = VideoClip(make_frame, duration=duration).set_fps(self.config["fps"])
        clip = fadein(clip, 0.8)
        self.clips.append(clip)

    def add_audio(self, final_clip, audio_path=None):
        """Add background music if available."""
        if not audio_path or not os.path.exists(audio_path):
            # Check assets/music folder
            music_dir = Path("assets/music")
            if music_dir.exists():
                tracks = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
                if tracks:
                    audio_path = str(tracks[0])

        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path).volumex(0.4)
            # Loop audio if shorter than video
            if audio.duration < final_clip.duration:
                loops = math.ceil(final_clip.duration / audio.duration)
                from moviepy.editor import concatenate_audioclips
                audio = concatenate_audioclips([audio] * loops)
            audio = audio.subclip(0, final_clip.duration)
            return final_clip.set_audio(audio)
        return final_clip

    def render(self, output_name=None, audio_path=None):
        if not self.clips:
            print("❌ No clips to render.")
            return None

        os.makedirs(self.config["output_dir"], exist_ok=True)
        name = output_name or f"journey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        out  = os.path.join(self.config["output_dir"], name)

        print(f"\n🎬  Rendering {len(self.clips)} clips → {out}")

        # Concatenate with crossfade
        final = concatenate_videoclips(self.clips, method="compose")
        final = self.add_audio(final, audio_path)
        final = fadeout(final, 0.8)

        final.write_videofile(
            out,
            fps=self.config["fps"],
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp_audio.m4a",
            remove_temp=True,
            verbose=False,
            logger=None,
        )
        print(f"✅  Done! Video saved to: {out}")
        return out

    def build_from_story(self, story_path=None):
        """Build a full video from a JSON story file."""
        story = self.story
        if story_path:
            with open(story_path) as f:
                story = json.load(f)

        if not story:
            print("❌ No story data found.")
            return

        cfg = story.get("settings", {})
        CONFIG["watermark"] = cfg.get("watermark", CONFIG["watermark"])

        theme = cfg.get("theme", "neon")
        self.renderer = FrameRenderer(self.config["width"], self.config["height"], theme)

        # Intro
        if story.get("title"):
            self.add_intro(
                story["title"],
                story.get("subtitle", ""),
                duration=story.get("intro_duration", 3.5)
            )

        # Slides
        for i, slide in enumerate(story.get("slides", []), 1):
            self.add_content_slide(
                image_path=slide.get("image"),
                caption=slide.get("caption", ""),
                location=slide.get("location", ""),
                step_num=i,
                duration=slide.get("duration", self.config["duration_per_slide"])
            )

        # Stats
        if story.get("stats"):
            self.add_stats(story["stats"], title=story.get("stats_title", "JOURNEY STATS"))

        # Render
        audio = story.get("audio") or cfg.get("audio")
        return self.render(story.get("output_name"), audio)


# ── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Journey Video Maker")
    parser.add_argument("--story",   "-s",  default="story.json", help="Path to story JSON")
    parser.add_argument("--demo",    "-d",  action="store_true",  help="Generate a demo video")
    parser.add_argument("--theme",   "-t",  default="neon",       help="Theme: neon|warm|dark|fire")
    parser.add_argument("--out",     "-o",  default=None,         help="Output filename")
    args = parser.parse_args()

    maker = JourneyVideoMaker()
    maker.renderer = FrameRenderer(CONFIG["width"], CONFIG["height"], args.theme)

    if args.demo:
        print("\n📽️   Generating DEMO journey video...\n")

        maker.add_intro(
            "MOTO JOURNEY",
            subtitle="2,000 KM ACROSS THE COUNTRY",
            duration=4.0
        )
        slides = [
            {"caption": "Day 1 – Left home at dawn", "location": "Nairobi"},
            {"caption": "The open road ahead 🏍️",    "location": "Nakuru"},
            {"caption": "Mountain pass at 3,000m",   "location": "Nyahururu"},
            {"caption": "Sunset by the lake ☀️",     "location": "Kisumu"},
            {"caption": "Final stretch – 200 km left","location": "Eldoret"},
        ]
        for i, s in enumerate(slides, 1):
            maker.add_content_slide(caption=s["caption"], location=s["location"], step_num=i)

        maker.add_stats({
            "Total Distance":  "2,048 km",
            "Days on Road":    "5 days",
            "Cities Crossed":  "12",
            "Fuel Used":       "~80L",
            "Best Day":        "Day 3 (520 km)",
        })

        maker.render(args.out or "demo_journey.mp4")

    elif os.path.exists(args.story):
        maker.build_from_story(args.story)
    else:
        print(f"\n⚠️  Story file '{args.story}' not found.")
        print("    Run with --demo to generate a sample video:")
        print("    python src/make_video.py --demo\n")
        print("    Or create a story.json — see story_example.json\n")
