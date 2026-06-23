from PIL import Image, ImageDraw, ImageFont  
import os  
  
img = Image.new('RGB', (1600, 900), '#EDE5D8')  
draw = ImageDraw.Draw(img) 
  
for i in range(0, 900, 4):  
    b = 230 + (i %% 8) * 2  
    draw.line([(0, i), (1600, i)], fill=(b, b-10, b-25))  
  
f10 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 10)  
f11 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 11)  
f12 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 12)  
f14 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)  
fb11 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 11)  
fb12 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 12)  
fb14 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 14)  
fb16 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 16)  
  
px, py, pw, ph = 80, 80, 300, 420  
draw.rectangle([px, py, px+pw, py+ph], fill='#8B1A1A')  
for i in range(0, ph, 3):  
    draw.line([(px+5, py+i), (px+pw-5, py+i)], fill='#9B2A2A', width=1)  
draw.rectangle([px+15, py+15, px+pw-15, py+ph-15], outline='#DAA520', width=2)  
