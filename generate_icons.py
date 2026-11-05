"""
Gym Tracker Pro - Luxury Icon Generator
Generates high-resolution adaptive PNG and SVG icons in Executive Royal Blue & Warm Beige.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, is_maskable=False):
    # Deep Royal Navy background #0A1128
    img = Image.new("RGBA", (size, size), color=(10, 17, 40, 255))
    draw = ImageDraw.Draw(img)

    # Padding calculation
    padding = size * 0.14 if is_maskable else size * 0.07
    center = size / 2

    # Outer decorative luxury ring in Warm Beige #E6D5B8
    outer_ring_radius = (size / 2) - padding
    draw.ellipse(
        [center - outer_ring_radius, center - outer_ring_radius, 
         center + outer_ring_radius, center + outer_ring_radius],
        outline=(230, 213, 184, 240),  # Warm Beige #E6D5B8
        width=max(2, int(size * 0.024))
    )

    # Inner concentric accent ring in Vibrant Royal Blue #2563EB
    inner_ring_radius = outer_ring_radius - size * 0.04
    draw.ellipse(
        [center - inner_ring_radius, center - inner_ring_radius, 
         center + inner_ring_radius, center + inner_ring_radius],
        outline=(37, 99, 235, 220),  # Royal Blue #2563EB
        width=max(1, int(size * 0.015))
    )

    # Central Athletic Shield in Deep Royal Blue with Warm Beige border
    shield_w = size * 0.44
    shield_top = center - size * 0.26
    shield_bottom = center + size * 0.28
    shield_mid_y = center + size * 0.08

    shield_points = [
        (center - shield_w / 2, shield_top),
        (center + shield_w / 2, shield_top),
        (center + shield_w / 2, shield_mid_y),
        (center, shield_bottom),
        (center - shield_w / 2, shield_mid_y),
    ]
    # Draw Shield body
    draw.polygon(shield_points, fill=(16, 28, 61, 245), outline=(230, 213, 184, 255))

    # Barbell & Plates in Royal Blue and Warm Beige
    bar_thickness = max(3, int(size * 0.045))
    bar_length = size * 0.54
    
    # Central barbell line in Warm Porcelain Beige
    draw.line(
        [center - bar_length / 2, center, center + bar_length / 2, center],
        fill=(245, 235, 224, 255),
        width=bar_thickness
    )

    # Weights / plates on left and right
    plate_width = size * 0.075
    plate_height_large = size * 0.34
    plate_height_small = size * 0.24

    # Left outer plate (Warm Beige #E6D5B8)
    draw.rounded_rectangle(
        [center - bar_length / 2, center - plate_height_small / 2, 
         center - bar_length / 2 + plate_width, center + plate_height_small / 2],
        radius=max(2, int(size * 0.02)),
        fill=(230, 213, 184, 255)
    )
    # Left inner plate (Vibrant Royal Blue #2563EB with Beige rim)
    draw.rounded_rectangle(
        [center - bar_length / 2 + plate_width * 1.25, center - plate_height_large / 2, 
         center - bar_length / 2 + plate_width * 2.35, center + plate_height_large / 2],
        radius=max(3, int(size * 0.025)),
        fill=(37, 99, 235, 255),
        outline=(245, 235, 224, 230),
        width=max(1, int(size * 0.01))
    )

    # Right inner plate (Vibrant Royal Blue #2563EB with Beige rim)
    draw.rounded_rectangle(
        [center + bar_length / 2 - plate_width * 2.35, center - plate_height_large / 2, 
         center + bar_length / 2 - plate_width * 1.25, center + plate_height_large / 2],
        radius=max(3, int(size * 0.025)),
        fill=(37, 99, 235, 255),
        outline=(245, 235, 224, 230),
        width=max(1, int(size * 0.01))
    )
    # Right outer plate (Warm Beige #E6D5B8)
    draw.rounded_rectangle(
        [center + bar_length / 2 - plate_width, center - plate_height_small / 2, 
         center + bar_length / 2, center + plate_height_small / 2],
        radius=max(2, int(size * 0.02)),
        fill=(230, 213, 184, 255)
    )

    # Central Crest: Polished Chevron & Star in Warm Cream Beige
    crest_pts = [
        (center, center - size * 0.20),
        (center + size * 0.10, center - size * 0.06),
        (center + size * 0.05, center - size * 0.06),
        (center, center - size * 0.12),
        (center - size * 0.05, center - size * 0.06),
        (center - size * 0.10, center - size * 0.06),
    ]
    draw.polygon(crest_pts, fill=(245, 235, 224, 255), outline=(37, 99, 235, 200))

    # Bottom chevron / banner
    lower_pts = [
        (center - size * 0.08, center + size * 0.08),
        (center, center + size * 0.20),
        (center + size * 0.08, center + size * 0.08),
        (center + size * 0.05, center + size * 0.08),
        (center, center + size * 0.15),
        (center - size * 0.05, center + size * 0.08),
    ]
    draw.polygon(lower_pts, fill=(230, 213, 184, 255))

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
