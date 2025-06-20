import argparse
import os
import textwrap
import json
import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def apply_film_grain(image, opacity=0.15):
    """Applies a film grain effect to a PIL image."""
    width, height = image.size
    noise = np.random.normal(loc=128, scale=300, size=(height, width)).clip(0, 255).astype(np.uint8)
    grain = Image.fromarray(noise, mode="L").convert("RGB")
    return Image.blend(image, grain, opacity)

def create_quote_image(quote, author, background_path, output_path,
                       font_path, quote_size, width, height):
    # Load background image
    bg = Image.open(background_path).convert("RGB")

    # Resize proportionally to cover
    bg_ratio = bg.width / bg.height
    canvas_ratio = width / height

    if bg_ratio > canvas_ratio:
        scale = height / bg.height
    else:
        scale = width / bg.width

    new_w = int(bg.width * scale)
    new_h = int(bg.height * scale)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)

    # Crop to center
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    bg = bg.crop((left, top, left + width, top + height))

    # Add translucent overlay
    
    # overlay = Image.new("RGBA", bg.size, (0, 0, 0, 120))
   # bg = bg.convert("RGBA")
    # bg = Image.alpha_composite(bg, overlay).convert("RGB")

    draw = ImageDraw.Draw(bg)
    font = ImageFont.truetype(font_path, quote_size)

    # Wrap and measure quote
    wrapped_quote = textwrap.fill(quote, width=40)
    quote_bbox = draw.textbbox((0, 0), wrapped_quote, font=font, spacing=8)
    quote_w = quote_bbox[2] - quote_bbox[0]
    quote_h = quote_bbox[3] - quote_bbox[1]
    quote_x = (width - quote_w) / 2
    quote_y = (height - quote_h) / 2

    draw.multiline_text(
        (quote_x, quote_y),
        wrapped_quote,
        font=font,
        fill="white",
        align="center",
        spacing=30
    )

    # Author near bottom
    author_text = f"— {author}"
    author_bbox = draw.textbbox((0, 0), author_text, font=font)
    author_w = author_bbox[2] - author_bbox[0]
    author_h = author_bbox[3] - author_bbox[1]
    author_x = (width - author_w) / 2
    author_y = height - 100 - author_h

    draw.text((author_x, author_y), author_text, font=font, fill="#DDDDDD")

    # Apply grain if enabled
    bg = apply_film_grain(bg)

    # Save output
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
    parser.add_argument("--batch", help="Path to JSON or YAML file for batch quote generation")

    args = parser.parse_args()

    if args.batch:
        quotes = load_quotes_from_file(args.batch)
        for i, entry in enumerate(quotes):
            quote = entry["quote"]
            author = entry["author"]
            background = entry["background"]
            output = entry.get("output", f"output/quote_{i + 1}.png")

            create_quote_image(
                quote, author, background, output,
                args.font, args.quote_size, args.width, args.height,
            )
    elif args.quote and args.author and args.background and args.output:
        create_quote_image(
            args.quote, args.author, args.background, args.output,
            args.font, args.quote_size, args.width, args.height
        )
    else:
        parser.print_help()
