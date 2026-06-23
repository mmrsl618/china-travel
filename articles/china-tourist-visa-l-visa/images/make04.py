from PIL import Image, ImageDraw, ImageFont 
import os, random 
random.seed(42) 
img = Image.new('RGB', (1600, 900), '#E8DFD0') 
draw = ImageDraw.Draw(img) 
f10 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 10) 
f11 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 11) 
f12 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 12) 
fb11 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 11) 
fb12 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 12) 
fb14 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 14) 
fb16 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 16) 
fb20 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20) 
 
# Draw wood table background 
for i in range(0, 900, 3): 
    v = 225 + ((i * 7 + random.randint(0, 3)) % 10) 
    draw.line([(0, i), (1600, i)], fill=(v, v-8, v-22)) 
 
# PASSPORT COVER 
px, py, pw, ph = 100, 100, 280, 390 
draw.rectangle([px, py, px+pw, py+ph], fill='#8B1A1A') 
draw.rectangle([px+12, py+12, px+pw-12, py+ph-12], outline='#DAA520', width=2) 
draw.text((px+pw//2-100, py+60), 'PEOPLES REPUBLIC OF CHINA', fill='#DAA520', font=fb14) 
# Emblem 
ecc, ecy, er = px+pw//2, py+100, 32 
draw.ellipse([ecc-er, ecy-er, ecc+er, ecy+er], fill='#DAA520') 
draw.ellipse([ecc-er+5, ecy-er+5, ecc+er-5, ecy+er-5], fill='#8B1A1A') 
draw.ellipse([ecc-3, ecy-3, ecc+3, ecy+3], fill='#DAA520') 
draw.text((px+pw//2-55, py+155), 'PASSPORT', fill='#DAA520', font=fb20) 
# Chip icon 
cx, cy2 = px+pw//2-12, py+ph-70 
draw.rectangle([cx, cy2, cx+24, cy2+18], fill='#DAA520') 
draw.rectangle([cx+2, cy2+2, cx+22, cy2+16], fill='#8B1A1A') 
 
# VISA PAGE 
vx, vy, vw, vh = 420, 100, 380, 390 
draw.rectangle([vx, vy, vx+vw, vy+vh], fill='#FFF8F0') 
draw.text((vx+15, vy+12), 'VISAS AND EXTENSIONS', fill='#333333', font=fb12) 
draw.line([(vx+15, vy+30), (vx+vw-15, vy+30)], fill='#cccccc', width=1) 
# Red visa stamp 
sx, sy, sw, sh = vx+25, vy+45, 190, 150 
draw.ellipse([sx, sy, sx+sw, sy+sh], outline='#CC0000', width=3) 
