from PIL import Image, ImageDraw, ImageFont

img = Image.open(r'E:\项目库\china-travel-website\images\visa-guide-02-visa-types-comparison.png').convert('RGBA')
draw = ImageDraw.Draw(img)

# Find and recolor "Best for" text in blue card (left)
# The blue card is roughly x: 40-320, y: 150-500
# We need to darken the light blue text
# Let's scan the blue card area and change light blue to darker blue
pixels = img.load()
w, h = img.size

# Blue card area: approximately left third
for y in range(h):
    for x in range(int(w * 0.05), int(w * 0.35)):
        r, g, b, a = pixels[x, y]
        # Light blue text color (approximately)
        # The "Best for" text is light blue on light blue bg
        # Target: darken the blue text while keeping it readable
        if a > 100 and b > 180 and g > 220 and r < 180:
            # Darken to a more saturated blue
            pixels[x, y] = (30, 100, 200, a)

img.save(r'E:\项目库\china-travel-website\images\visa-guide-02-visa-types-comparison.png', 'PNG')
print("Done fixing visa-guide-02")
