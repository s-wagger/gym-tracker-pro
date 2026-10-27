"""
Gym Tracker Pro - Icon Generator
Generates high-resolution adaptive PNG and SVG icons for PWA compliance.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, is_maskable=False):
    # Base image with high-contrast dark slate background
    img = Image.new("RGBA", (size, size), color=(18, 18, 18, 255))
    draw = ImageDraw.Draw(img)

    # Padding calculation
    padding = size * 0.15 if is_maskable else size * 0.08
    center = size / 2

    # Outer decorative glow ring
    ring_radius = (size / 2) - padding
    draw.ellipse(
        [center - ring_radius, center - ring_radius, center + ring_radius, center + ring_radius],
        outline=(204, 255, 0, 180),  # #CCFF00 with alpha
        width=max(2, int(size * 0.025))
    )

    # Stylized Dumbbell / Hex weights in Neon Lime #CCFF00
    bar_thickness = max(4, int(size * 0.06))
    bar_length = size * 0.52
    
    # Central barbell
    draw.line(
        [center - bar_length / 2, center, center + bar_length / 2, center],
        fill=(255, 255, 255, 240),
        width=bar_thickness
    )

    # Weights / plates on left and right
    plate_width = size * 0.08
    plate_height_large = size * 0.38
    plate_height_small = size * 0.26

    # Left outer plate
    draw.rounded_rectangle(
        [center - bar_length / 2, center - plate_height_small / 2, 
         center - bar_length / 2 + plate_width, center + plate_height_small / 2],
        radius=max(2, int(size * 0.02)),
        fill=(255, 215, 0, 255) # Gold accent #FFD700
    )
    # Left inner plate (Large)
    draw.rounded_rectangle(
        [center - bar_length / 2 + plate_width * 1.2, center - plate_height_large / 2, 
         center - bar_length / 2 + plate_width * 2.2, center + plate_height_large / 2],
        radius=max(3, int(size * 0.025)),
        fill=(204, 255, 0, 255) # Neon Lime #CCFF00
    )

    # Right inner plate (Large)
    draw.rounded_rectangle(
        [center + bar_length / 2 - plate_width * 2.2, center - plate_height_large / 2, 
         center + bar_length / 2 - plate_width * 1.2, center + plate_height_large / 2],
        radius=max(3, int(size * 0.025)),
        fill=(204, 255, 0, 255) # Neon Lime #CCFF00
    )
    # Right outer plate
    draw.rounded_rectangle(
        [center + bar_length / 2 - plate_width, center - plate_height_small / 2, 
         center + bar_length / 2, center + plate_height_small / 2],
        radius=max(2, int(size * 0.02)),
        fill=(255, 215, 0, 255) # Gold accent #FFD700
    )

    # Central energetic lightning bolt
    bolt_points = [
        (center + size * 0.03, center - size * 0.22),
        (center - size * 0.09, center + size * 0.02),
        (center - size * 0.01, center + size * 0.02),
        (center - size * 0.04, center + size * 0.22),
        (center + size * 0.09, center - size * 0.02),
        (center + size * 0.01, center - size * 0.02),
    ]
    draw.polygon(bolt_points, fill=(204, 255, 0, 255), outline=(18, 18, 18, 255))

    return img

if __name__ == "__main__":
    os.makedirs("static/icons", exist_ok=True)
    
    # Generate 192x192
    icon_192 = create_icon(192)
    icon_192.save("static/icons/icon-192.png", "PNG")
    print("Created static/icons/icon-192.png")

    # Generate 512x512
    icon_512 = create_icon(512)
    icon_512.save("static/icons/icon-512.png", "PNG")
    print("Created static/icons/icon-512.png")

    # Generate Maskable 512x512
    icon_maskable = create_icon(512, is_maskable=True)
    icon_maskable.save("static/icons/icon-maskable.png", "PNG")
    print("Created static/icons/icon-maskable.png")

    # Generate Apple Touch Icon (180x180)
    icon_apple = create_icon(180)
    icon_apple.save("static/icons/apple-touch-icon.png", "PNG")
    print("Created static/icons/apple-touch-icon.png")

    # Generate favicon (64x64)
    icon_fav = create_icon(64)
    icon_fav.save("static/icons/favicon.png", "PNG")
    print("Created static/icons/favicon.png")
