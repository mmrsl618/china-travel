#!/usr/bin/env python3
"""Fix visa-guide-02: darken the 'Best for' text in all three cards."""
from PIL import Image, ImageDraw
import os

input_path = r'E:\项目库\china-travel-website\images\visa-guide-02-visa-types-comparison.png'
output_path = input_path

img = Image.open(input_path).convert('RGBA')
pixels = img.load()
w, h = img.size

# Strategy: scan each card region for light-colored text and darken it
# Card regions (approximate, based on the original image layout):
# Blue card: x=30..310, Green card: x=330..610, Purple card: x=630..910

darkened_count = 0

for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if a < 128:
            continue
        
        # Detect light-colored text (not white background, not header colors)
        # Background is very light: high R,G,B values
        # Light blue/green/purple text: tinted but bright
        
        # Skip white/near-white pixels (background)
        if r > 240 and g > 240 and b > 240:
            continue
        
        # Skip the header bar colors (solid dark colors)
        # Blue header: r~50,g~150,b~220
        # Green header: r~40,g~190,b~100
        # Purple header: r~160,g~100,b~200
        # These have moderate brightness - skip if too saturated
        
        avg = (r + g + b) / 3
        max_ch = max(r, g, b)
        min_ch = min(r, g, b)
        saturation = (max_ch - min_ch) / max_ch if max_ch > 0 else 0
        
        # Light text = low saturation or moderate saturation with high brightness
        # We want to catch the light blue/green/purple text
        # Header bars have higher saturation, body text has lower saturation
        
        # Target: light colored text with brightness between 120-220 and low-moderate saturation
        if 120 < avg < 230 and saturation < 0.5:
            # This is likely light text - darken it
            factor = 0.4  # darken significantly
            new_r = max(0, int(r * factor))
            new_g = max(0, int(g * factor))
            new_b = max(0, int(b * factor))
            pixels[x, y] = (new_r, new_g, new_b, a)
            darkened_count += 1

img.save(output_path, 'PNG')
print(f"Darkened {darkened_count} pixels in visa-guide-02")
