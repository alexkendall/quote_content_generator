import argparse
import os
import textwrap
import json
import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageStat
import colorsys


def apply_film_grain(image, opacity=0.15):
    width, height = image.size
    noise = np.random.normal(loc=128, scale=600, size=(height, width)).clip(0, 255).astype(np.uint8)
    grain = Image.fromarray(noise, mode="L").convert("RGB")
    return Image.blend(image, grain, opacity)

def get_average_color(image):
    stat = ImageStat.Stat(image)
    r, g, b = [int(c) for c in stat.mean[:3]]
    return (r, g, b)

def get_vibrant_color(image):
    small_img = image.resize((64, 64))
    pixels = np.array(small_img).reshape((-1, 3))
    max_saturation = -1
    vibrant = (255, 255, 255)

    for r, g, b in pixels:
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        if s > max_saturation and l > 0.2 and l < 0.8:
            max_saturation = s
            vibrant = (r, g, b)

    return vibrant

def get_contrasting_text_color(bg_color):
    r, g, b = [int(c) for c in bg_color]
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 150 else "white"

def draw_pill(draw, text, font, x, y, bg_color):
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    pill_w = text_w + 80
    pill_h = text_h + 40

    x1 = x + pill_w
    y1 = y + pill_h

    draw.rounded_rectangle([(x, y), (x1, y1)], radius=pill_h // 2, fill=bg_color)

    text_x = x + (pill_w - text_w) / 2
    text_y = y + (pill_h - text_h) / 2
    text_color = get_contrasting_text_color(bg_color)
    draw.text((text_x, text_y), text, font=font, fill=text_color)

def create_quote_image(quote, author, background_path, output_path,
                       font_path, quote_size, width, height, year=None, cast=None, director=None):
    bg = Image.open(background_path).convert("RGB")

    avg_color = get_average_color(bg)
    vibrant_color = get_vibrant_color(bg)

    bg_ratio = bg.width / bg.height
    canvas_ratio = width / height

    if bg_ratio > canvas_ratio:
        scale = height / bg.height
    else:
        scale = width / bg.width

    new_w = int(bg.width * scale)
    new_h = int(bg.height * scale)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    bg = bg.crop((left, top, left + width, top + height))

    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 60))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay).convert("RGB")

    bg = apply_film_grain(bg)

    draw = ImageDraw.Draw(bg)
    font = ImageFont.truetype(font_path, quote_size)

    wrapped_quote = textwrap.fill(quote, width=40)
    quote_bbox = draw.textbbox((0, 0), wrapped_quote, font=font, spacing=8)
    quote_w = quote_bbox[2] - quote_bbox[0]
    quote_h = quote_bbox[3] - quote_bbox[1]
    quote_x = (width - quote_w) / 2
    quote_y = (height - quote_h) / 2

    author_text = author
    author_bbox = draw.textbbox((0, 0), author_text, font=font)
    author_w = author_bbox[2] - author_bbox[0]
    author_h = author_bbox[3] - author_bbox[1]
    author_x = (width - author_w) / 2
    author_y = height - 150 - author_h

    pill_font = ImageFont.truetype(font_path, size=int(quote_size * 0.6))

    if year:
        draw_pill(draw, str(year), pill_font, x=width - 100 - 140, y=100, bg_color=avg_color)

    if director:
        draw_pill(draw, f"Dir. {director}", pill_font, x=100, y=100, bg_color=vibrant_color)

    draw.multiline_text(
        (quote_x, quote_y),
        wrapped_quote,
        font=font,
        fill="white",
        align="left",
        spacing=30
    )

    draw.text((author_x, author_y), author_text, font=font, fill="#DDDDDD")

    if cast:
        cast_font = ImageFont.truetype(font_path, int(quote_size * 0.65))
        cast_text = cast
        cast_bbox = draw.textbbox((0, 0), cast_text, font=cast_font)
        cast_w = cast_bbox[2] - cast_bbox[0]
        cast_h = cast_bbox[3] - cast_bbox[1]
        cast_x = quote_x + quote_w - cast_w
        cast_y = quote_y + quote_h + 100

        draw.text((cast_x, cast_y), cast_text, font=cast_font, fill="#AAAAAA")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bg.save(output_path)
    print(f"✅ Saved: {output_path}")

def load_quotes_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    with open(filepath, 'r') as f:
        if ext == ".json":
            return json.load(f)
        elif ext in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Use JSON or YAML.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate quote overlay image(s).")
    parser.add_argument("--quote", help="The quote text")
    parser.add_argument("--author", help="Name of the person being quoted")
    parser.add_argument("--background", help="Path to background image")
    parser.add_argument("--output", help="Path to save output image")
    parser.add_argument("--font", default="fonts/JosefinSans-SemiBold.ttf", help="Path to .ttf font file")
    parser.add_argument("--quote_size", type=int, default=50)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--grain", action="store_true", help="Apply film grain effect")
    parser.add_argument("--year", help="Optional year to display in top-right corner")
    parser.add_argument("--cast", help="Optional cast member to display near quote")
    parser.add_argument("--director", help="Optional director name to display in top-left corner")
    parser.add_argument("--batch", help="Path to JSON or YAML file for batch quote generation")

    args = parser.parse_args()

    if args.batch:
        quotes = load_quotes_from_file(args.batch)
        for i, entry in enumerate(quotes):
            quote = entry["quote"]
            author = entry["author"]
            background = entry["background"]
            output = entry.get("output", f"output/quote_{i + 1}.png")
            year = entry.get("year")
            cast = entry.get("cast")
            director = entry.get("director")

            create_quote_image(
                quote, author, background, output,
                args.font, args.quote_size, args.width, args.height,
                year=year, cast=cast, director=director
            )
    elif args.quote and args.author and args.background and args.output:
        create_quote_image(
            args.quote, args.author, args.background, args.output,
            args.font, args.quote_size, args.width, args.height,
            year=args.year, cast=args.cast, director=args.director
        )
    else:
        parser.print_help()
