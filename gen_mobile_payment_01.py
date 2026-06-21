"""Generate mobile-payment-01: Alipay scan-to-pay at street food market."""
import os
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = r"E:\项目库\china-travel-website\images"
W, H = 390, 696

# Fonts
FONT_ZH = r"C:\Windows\Fonts\msyh.ttc"
FONT_ZH_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

def make_font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except Exception:
        return ImageFont.load_default()

def make_zh_font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_ZH_BOLD if bold else FONT_ZH, size)
    except Exception:
        return ImageFont.load_default()

F11 = make_font(11)
F12 = make_font(12)
F13 = make_font(13)
F14 = make_font(14)
F16 = make_font(16)
F18 = make_font(18)
F20 = make_font(20)
F22 = make_font(22)
F28 = make_font(28)
F32 = make_font(32)
F40 = make_font(40)

ZF12 = make_zh_font(12)
ZF14 = make_zh_font(14)
ZF14B = make_zh_font(14, bold=True)
ZF16 = make_zh_font(16)
ZF16B = make_zh_font(16, bold=True)
ZF18 = make_zh_font(18)
ZF20 = make_zh_font(20)
ZF22 = make_zh_font(22)
ZF24 = make_zh_font(24)
ZF28 = make_zh_font(28)
ZF32 = make_zh_font(32)

ALIPAY_GREEN = "#1677FF"
ALIPAY_DARK = "#001529"
ALIPAY_GRAY = "#999999"
ALIPAY_LIGHT_GRAY = "#f5f5f5"

def draw_status_bar(draw):
    """Draw iPhone status bar."""
    # Signal
    for i in range(4):
        h = 4 + i * 3
        draw.rectangle([14 + i*3, 14-h, 16 + i*3, 14], fill="#000")
    # WiFi
    draw.arc([30, 12, 38, 20], 200, 340, fill="#000", width=1)
    draw.arc([32, 14, 36, 18], 200, 340, fill="#000", width=1)
    draw.point([34, 20], fill="#000")
    # Time
    draw.text((172, 10), "9:41", fill="#000", font=F12)
    # Battery
    draw.rounded_rectangle([(312, 8), (334, 18)], radius=3, outline="#000", width=1)
    draw.rectangle([(332, 10), (334, 16)], fill="#000")
    draw.rectangle([(314, 10), (330, 16)], fill="#000")

def draw_qr_code(draw, cx, cy, size):
    """Draw a simple QR code pattern."""
    half = size // 2
    # Position detection patterns (3 corners)
    pos_size = size // 3
    positions = [(cx - half, cy - half), (cx + half - pos_size, cy - half),
                 (cx - half, cy + half - pos_size)]
    for px, py in positions:
        draw.rectangle([px, py, px+pos_size, py+pos_size], fill="#000")
        inner = pos_size - 6
        offset = 3
        draw.rectangle([px+offset, py+offset, px+offset+inner, py+offset+inner], fill="#fff")
        draw.rectangle([px+offset+2, py+offset+2, px+offset+inner-2, py+offset+inner-2], fill="#000")
    
    # Data modules
    module_size = 3
    rng = 42
    for row in range(size // module_size):
        for col in range(size // module_size):
            # Skip position detection areas
            skip = False
            for px, py in positions:
                rx = (px <= col*module_size < px+pos_size)
                ry = (py <= row*module_size < py+pos_size)
                if rx and ry:
                    skip = True
                    break
            if skip:
                continue
            rng = (rng * 1103515245 + 12345) & 0x7fffffff
            if rng % 3 != 0:
                draw.rectangle([cx - half + col*module_size, cy - half + row*module_size,
                               cx - half + col*module_size + module_size - 1,
                               cy - half + row*module_size + module_size - 1], fill="#000")

def generate():
    # Create base image: phone screen on blurred street food market background
    # Background: warm-toned street food market scene
    bg = Image.new('RGB', (W, H), '#2a1f14')
    draw = ImageDraw.Draw(bg)
    
    # Draw a warm blurred market scene background
    # Warm ambient glow
    for i in range(20):
        y = i * 35
        alpha_val = int(40 + i * 2)
        draw.rectangle([0, y, W, y+34], fill=(int(60+i*2), int(40+i), int(20+i)))
    
    # Some warm light spots (bokeh effect)
    import random
    random.seed(77)
    for _ in range(15):
        x = random.randint(0, W)
        y = random.randint(0, H)
        r = random.randint(10, 30)
        brightness = random.randint(80, 150)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(brightness, brightness-20, brightness-50))
    
    # Phone frame (slight shadow)
    phone_x, phone_y = 25, 10
    phone_w, phone_h = W - 50, H - 20
    
    # Shadow
    draw.rounded_rectangle([phone_x+4, phone_y+4, phone_x+phone_w+4, phone_y+phone_h+4], radius=30, fill="#000000")
    
    # Phone body (black bezel)
    draw.rounded_rectangle([phone_x, phone_y, phone_x+phone_w, phone_y+phone_h], radius=30, fill="#1a1a1a")
    
    # Screen area (white)
    screen_margin = 8
    draw.rounded_rectangle([phone_x+screen_margin, phone_y+screen_margin,
                            phone_x+screen_margin+phone_w-2*screen_margin,
                            phone_y+screen_margin+phone_h-2*screen_margin],
                           radius=22, fill="#ffffff")
    
    # Now draw the Alipay UI inside the screen
    sw = phone_w - 2*screen_margin  # screen width
    sh = phone_h - 2*screen_margin  # screen height
    sx = phone_x + screen_margin   # screen left
    sy = phone_y + screen_margin   # screen top
    
    screen_img = Image.new('RGB', (sw, sh), '#ffffff')
    sdraw = ImageDraw.Draw(screen_img)
    
    # Status bar
    draw_status_bar(sdraw)
    
    # Header - Alipay blue
    sdraw.rectangle([0, 20, sw, 56], fill=ALIPAY_GREEN)
    sdraw.line([(0, 56), (sw, 56)], fill="#0d66e0", width=1)
    # Back arrow
    sdraw.line([(14, 32), (10, 38), (14, 44)], fill="#ffffff", width=2)
    # Title
    title_w = sdraw.textlength("扫一扫", font=ZF18)
    sdraw.text(((sw - title_w)//2, 28), "扫一扫", fill="#ffffff", font=ZF18)
    # Camera icon on right
    sdraw.rectangle([(sw-44, 30), (sw-24, 48)], outline="#ffffff", width=2)
    sdraw.line([(sw-34, 30), (sw-34, 48)], fill="#ffffff", width=2)
    sdraw.line([(sw-44, 39), (sw-24, 39)], fill="#ffffff", width=2)
    
    # Scanning area with QR code already scanned
    scan_area_y = 72
    scan_box_size = 200
    scan_box_x = (sw - scan_box_size) // 2
    scan_box_y = scan_area_y
    
    # "Scan area" label
    sdraw.text((16, scan_area_y + 2), "对准二维码扫描", fill=ALIPAY_GRAY, font=ZF14)
    
    # Scanning box with corner markers
    corner_len = 20
    # Top-left
    sdraw.line([(scan_box_x, scan_box_y+corner_len), (scan_box_x, scan_box_y),
                (scan_box_x+corner_len, scan_box_y)], fill=ALIPAY_GREEN, width=3)
    # Top-right
    sdraw.line([(scan_box_x+scan_box_size-corner_len, scan_box_y),
                (scan_box_x+scan_box_size, scan_box_y),
                (scan_box_x+scan_box_size, scan_box_y+corner_len)], fill=ALIPAY_GREEN, width=3)
    # Bottom-left
    sdraw.line([(scan_box_x, scan_box_y+scan_box_size-corner_len),
                (scan_box_x, scan_box_y+scan_box_size),
                (scan_box_x+corner_len, scan_box_y+scan_box_size)], fill=ALIPAY_GREEN, width=3)
    # Bottom-right
    sdraw.line([(scan_box_x+scan_box_size-corner_len, scan_box_y+scan_box_size),
                (scan_box_x+scan_box_size, scan_box_y+scan_box_size),
                (scan_box_x+scan_box_size, scan_box_y+scan_box_size-corner_len)], fill=ALIPAY_GREEN, width=3)
    
    # Scanning line animation effect (horizontal line in middle)
    mid_y = scan_box_y + scan_box_size // 2
    sdraw.line([(scan_box_x, mid_y), (scan_box_x+scan_box_size, mid_y)], fill=ALIPAY_GREEN, width=2)
    
    # Draw the QR code inside the scan box
    qr_center_x = scan_box_x + scan_box_size // 2
    qr_center_y = scan_box_y + scan_box_size // 2
    qr_size = scan_box_size - 30
    draw_qr_code(sdraw, qr_center_x, qr_center_y, qr_size)
    
    # Below scan box: payment confirmation area (already scanned!)
    confirm_y = scan_box_y + scan_box_size + 20
    
    # Green success banner
    sdraw.rounded_rectangle([(12, confirm_y), (sw-12, confirm_y+36), ], radius=8, fill="#e8f5e9")
    sdraw.text((24, confirm_y+8), "✓ 已扫描商家收款码", fill="#2e7d32", font=ZF14)
    
    # Merchant name
    merch_y = confirm_y + 50
    sdraw.text((20, merch_y), "商家名称", fill=ALIPAY_GRAY, font=ZF12)
    sdraw.text((20, merch_y+22), "老王煎饼果子", fill=ALIPAY_DARK, font=ZF24)
    
    # Amount
    amt_y = merch_y + 70
    sdraw.text((20, amt_y), "收款金额", fill=ALIPAY_GRAY, font=ZF12)
    sdraw.text((20, amt_y+22), "¥ 28.00", fill="#e63946", font=ZF32)
    
    # Transaction note
    note_y = amt_y + 70
    sdraw.text((20, note_y), "备注：扫码付款", fill=ALIPAY_GRAY, font=ZF12)
    
    # Confirm payment button at bottom
    btn_y = note_y + 50
    btn_h = 48
    sdraw.rounded_rectangle([(20, btn_y), (sw-20, btn_y+btn_h), ], fill=ALIPAY_GREEN, radius=24)
    btn_text = "确认付款"
    btn_tw = sdraw.textlength(btn_text, font=ZF20)
    sdraw.text(((sw - btn_tw)//2, btn_y+12), btn_text, fill="#ffffff", font=ZF20)
    
    # Bottom safe area indicator
    sdraw.rounded_rectangle([(sw//2 - 40, H-36), (sw//2 + 40, H-32)], radius=4, fill="#cccccc")
    
    # Composite screen onto phone
    bg.paste(screen_img, (sx, sy))
    
    # Save
    out_path = os.path.join(IMAGES_DIR, "mobile-payment-01-street-food-market.png")
    bg.save(out_path, "PNG")
    print(f"Generated: {out_path}")

if __name__ == "__main__":
    generate()
