"""Composite street food market background with Alipay UI overlay."""
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = r"E:\项目库\china-travel-website\images"
W, H = 390, 696

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
F14 = make_font(14)
F16 = make_font(16)
F18 = make_font(18)
F20 = make_font(20)
F22 = make_font(22)
F28 = make_font(28)
F32 = make_font(32)

ZF12 = make_zh_font(12)
ZF14 = make_zh_font(14)
ZF16 = make_zh_font(16)
ZF18 = make_zh_font(18)
ZF20 = make_zh_font(20)
ZF22 = make_zh_font(22)
ZF24 = make_zh_font(24)
ZF28 = make_zh_font(28)
ZF32 = make_zh_font(32)

ALIPAY_GREEN = "#1677FF"
ALIPAY_DARK = "#001529"
ALIPAY_GRAY = "#999999"

def draw_qr_code(draw, cx, cy, size):
    """Draw a simple QR code pattern."""
    half = size // 2
    pos_size = size // 3
    positions = [(cx - half, cy - half), (cx + half - pos_size, cy - half),
                 (cx - half, cy + half - pos_size)]
    for px, py in positions:
        draw.rectangle([px, py, px+pos_size, py+pos_size], fill="#000")
        inner = pos_size - 6
        offset = 3
        draw.rectangle([px+offset, py+offset, px+offset+inner, py+offset+inner], fill="#fff")
        draw.rectangle([px+offset+2, py+offset+2, px+offset+inner-2, py+offset+inner-2], fill="#000")
    
    module_size = 3
    rng = 42
    for row in range(size // module_size):
        for col in range(size // module_size):
            skip = False
            for px, py in positions:
                if (px <= col*module_size < px+pos_size) and (py <= row*module_size < py+pos_size):
                    skip = True
                    break
            if skip:
                continue
            rng = (rng * 1103515245 + 12345) & 0x7fffffff
            if rng % 3 != 0:
                draw.rectangle([cx - half + col*module_size, cy - half + row*module_size,
                               cx - half + col*module_size + module_size - 1,
                               cy - half + row*module_size + module_size - 1], fill="#000")

def draw_phone_screen(draw, sw, sh, sx, sy):
    """Draw the complete Alipay UI on the given draw object at (sx,sy) with size (sw,sh)."""
    # White screen background
    draw.rectangle([sx, sy, sx+sw, sy+sh], fill="#ffffff")
    
    # Status bar
    # Signal
    for i in range(4):
        h = 4 + i * 3
        draw.rectangle([sx+14+i*3, sy+14-h, sx+16+i*3, sy+14], fill="#000")
    # WiFi
    draw.arc([sx+30, sy+12, sx+38, sy+20], 200, 340, fill="#000", width=1)
    draw.arc([sx+32, sy+14, sx+36, sy+18], 200, 340, fill="#000", width=1)
    draw.point((sx+34, sy+20), fill="#000")
    # Time
    draw.text((sx+172, sy+10), "9:41", fill="#000", font=F12)
    # Battery
    draw.rounded_rectangle([(sx+312, sy+8), (sx+334, sy+18)], radius=3, outline="#000", width=1)
    draw.rectangle([(sx+332, sy+10), (sx+334, sy+16)], fill="#000")
    draw.rectangle([(sx+314, sy+10), (sx+330, sy+16)], fill="#000")
    
    # Header - Alipay blue
    draw.rectangle([sx, sy+20, sx+sw, sy+56], fill=ALIPAY_GREEN)
    draw.line([(sx, sy+56), (sx+sw, sy+56)], fill="#0d66e0", width=1)
    # Back arrow
    draw.line([(sx+14, sy+32), (sx+10, sy+38), (sx+14, sy+44)], fill="#ffffff", width=2)
    # Title centered
    title = "扫一扫"
    title_w = draw.textlength(title, font=ZF18)
    draw.text(((sx + sw - title_w)//2, sy+28), title, fill="#ffffff", font=ZF18)
    # Camera icon on right
    cpx = sx + sw - 44
    draw.rectangle([cpx, sy+30, cpx+20, sy+48], outline="#ffffff", width=2)
    draw.line([(cpx+10, sy+30), (cpx+10, sy+48)], fill="#ffffff", width=2)
    draw.line([(cpx, sy+39), (cpx+20, sy+39)], fill="#ffffff", width=2)
    
    # Scanning area
    scan_area_y = sy + 72
    scan_box_size = 200
    scan_box_x = sx + (sw - scan_box_size) // 2
    scan_box_y = scan_area_y
    
    draw.text((sx+16, scan_area_y+2), "对准二维码扫描", fill=ALIPAY_GRAY, font=ZF14)
    
    # Corner markers
    cl = 20
    # TL
    draw.line([(scan_box_x, scan_box_y+cl), (scan_box_x, scan_box_y),
                (scan_box_x+cl, scan_box_y)], fill=ALIPAY_GREEN, width=3)
    # TR
    draw.line([(scan_box_x+scan_box_size-cl, scan_box_y),
                (scan_box_x+scan_box_size, scan_box_y),
                (scan_box_x+scan_box_size, scan_box_y+cl)], fill=ALIPAY_GREEN, width=3)
    # BL
    draw.line([(scan_box_x, scan_box_y+scan_box_size-cl),
                (scan_box_x, scan_box_y+scan_box_size),
                (scan_box_x+cl, scan_box_y+scan_box_size)], fill=ALIPAY_GREEN, width=3)
    # BR
    draw.line([(scan_box_x+scan_box_size-cl, scan_box_y+scan_box_size),
                (scan_box_x+scan_box_size, scan_box_y+scan_box_size),
                (scan_box_x+scan_box_size, scan_box_y+scan_box_size-cl)], fill=ALIPAY_GREEN, width=3)
    
    # Scan line
    mid_y = scan_box_y + scan_box_size // 2
    draw.line([(scan_box_x, mid_y), (scan_box_x+scan_box_size, mid_y)], fill=ALIPAY_GREEN, width=2)
    
    # QR code
    qr_cx = scan_box_x + scan_box_size // 2
    qr_cy = scan_box_y + scan_box_size // 2
    qr_sz = scan_box_size - 30
    draw_qr_code(draw, qr_cx, qr_cy, qr_sz)
    
    # Payment confirmation area
    confirm_y = scan_box_y + scan_box_size + 20
    
    # Success banner
    draw.rounded_rectangle([(sx+12, confirm_y), (sx+sw-12, confirm_y+36), ], radius=8, fill="#e8f5e9")
    draw.text((sx+24, confirm_y+8), "✓ 已扫描商家收款码", fill="#2e7d32", font=ZF14)
    
    # Merchant name
    merch_y = confirm_y + 50
    draw.text((sx+20, merch_y), "商家名称", fill=ALIPAY_GRAY, font=ZF12)
    draw.text((sx+20, merch_y+22), "老王煎饼果子", fill=ALIPAY_DARK, font=ZF24)
    
    # Amount
    amt_y = merch_y + 70
    draw.text((sx+20, amt_y), "收款金额", fill=ALIPAY_GRAY, font=ZF12)
    draw.text((sx+20, amt_y+22), "¥ 28.00", fill="#e63946", font=ZF32)
    
    # Note
    note_y = amt_y + 70
    draw.text((sx+20, note_y), "备注：扫码付款", fill=ALIPAY_GRAY, font=ZF12)
    
    # Confirm button
    btn_y = note_y + 50
    btn_h = 48
    draw.rounded_rectangle([(sx+20, btn_y), (sx+sw-20, btn_y+btn_h), ], fill=ALIPAY_GREEN, radius=24)
    btn_text = "确认付款"
    btn_tw = draw.textlength(btn_text, font=ZF20)
    draw.text(((sx + sw - btn_tw)//2, btn_y+12), btn_text, fill="#ffffff", font=ZF20)
    
    # Home indicator
    draw.rounded_rectangle([(sx+sw//2-40, sy+sh-36), (sx+sw//2+40, sy+sh-32)], radius=4, fill="#cccccc")


def main():
    # Load background
    bg = Image.open(r"E:\项目库\china-travel-website\images\mobile-payment-01-bg.png")
    bg = bg.resize((W, H), Image.LANCZOS)
    
    # Draw phone shadow and bezel
    phone_x, phone_y = 25, 10
    phone_w, phone_h = W - 50, H - 20
    
    # Darken and blur the background slightly to emphasize the phone
    draw_bg = ImageDraw.Draw(bg)
    # Draw phone shadow
    draw_bg.rounded_rectangle([phone_x-2, phone_y-2, phone_x+phone_w+2, phone_y+phone_h+2], radius=32, fill="#000000")
    
    # Phone bezel
    draw_bg.rounded_rectangle([phone_x, phone_y, phone_x+phone_w, phone_y+phone_h], radius=30, fill="#1a1a1a")
    
    # Screen dimensions
    screen_margin = 8
    sw = phone_w - 2*screen_margin
    sh = phone_h - 2*screen_margin
    sx = phone_x + screen_margin
    sy = phone_y + screen_margin
    
    # Create screen canvas
    screen = Image.new('RGB', (sw, sh), '#ffffff')
    sdraw = ImageDraw.Draw(screen)
    
    # Draw the Alipay UI
    draw_phone_screen(sdraw, sw, sh, 0, 0)
    
    # Paste screen onto phone
    bg.paste(screen, (sx, sy))
    
    # Save
    out_path = r"E:\项目库\china-travel-website\images\mobile-payment-01-street-food-market.png"
    bg.save(out_path, "PNG")
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
