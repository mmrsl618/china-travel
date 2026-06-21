from PIL import Image, ImageDraw, ImageFont
import os

img_path = r'E:\项目库\china-travel-website\images\visa-guide-02-visa-types-comparison.png'
img = Image.open(img_path).convert('RGBA')
draw = ImageDraw.Draw(img)

# Load fonts
try:
    font_large = ImageFont.truetype("arialbd.ttf", 28)
except:
    try:
        font_large = ImageFont.truetype("msyhbd.ttc", 28)
    except:
        font_large = ImageFont.load_default()

try:
    font_normal = ImageFont.truetype("arial.ttf", 16)
except:
    try:
        font_normal = ImageFont.truetype("msyh.ttc", 16)
    except:
        font_normal = ImageFont.load_default()

try:
    font_small = ImageFont.truetype("arial.ttf", 14)
except:
    try:
        font_small = ImageFont.truetype("msyh.ttc", 14)
    except:
        font_small = ImageFont.load_default()

w, h = img.size
pixels = img.load()

# Redraw "Best for" section in each card with darker colors
# Blue card (left): x ~ 40-320, y ~ 350-500
# Green card (middle): x ~ 340-620, y ~ 350-500  
# Purple card (right): x ~ 640-920, y ~ 350-500

cards = [
    {"x_start": 40, "x_end": 320, "color": (30, 100, 200), "label_color": (80, 80, 80)},
    {"x_start": 340, "x_end": 620, "color": (0, 150, 70), "label_color": (80, 80, 80)},
    {"x_start": 640, "x_end": 920, "color": (120, 60, 160), "label_color": (80, 80, 80)},
]

# Clear out the old "Best for" text areas first (light colored)
# Then redraw with dark colors
for i, card in enumerate(cards):
    # Scan and darken the "Best for" text area
    for y in range(int(h * 0.65), int(h * 0.85)):
        for x in range(card["x_start"] + 10, card["x_end"] - 10):
            r, g, b, a = pixels[x, y]
            if a > 50:
                # Check if it's light colored text (not background)
                brightness = (r + g + b) / 3
                if brightness > 150 and a > 100:
                    # This is likely light text - darken it
                    pixels[x, y] = (card["color"][0], card["color"][1], card["color"][2], a)

img.save(img_path, 'PNG')
print("Done fixing visa-guide-02")
