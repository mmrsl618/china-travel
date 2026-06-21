"""
Regenerate mobile-payment images 03, 05, 08.
Requirements:
- Realistic UI screenshot style (no illustrations/cartoon)
- No watermarks, no brand logos (Alipay/WeChat logos removed)
- Vertical 9:16 (390x693)
- Text fully readable, no overlap, no overflow
- PNG for images with QR codes/text, JPEG for others
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = r"E:\项目库\china-travel-website\images"
W, H = 390, 693

# Fonts
FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_ZH = r"C:\Windows\Fonts\msyh.ttc"
FONT_ZH_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

def make_font(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype(FONT_BOLD, size)
        return ImageFont.truetype(FONT_REG, size)
    except Exception:
        return ImageFont.load_default()

def make_zh_font(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype(FONT_ZH_BOLD, size)
        return ImageFont.truetype(FONT_ZH, size)
    except Exception:
        return ImageFont.load_default()

F10 = make_font(10)
F11 = make_font(11)
F12 = make_font(12)
F13 = make_font(13)
F14 = make_font(14)
F14B = make_font(14, bold=True)
F16 = make_font(16)
F16B = make_font(16, bold=True)
F18 = make_font(18)
F18B = make_font(18, bold=True)
F20 = make_font(20)
F22 = make_font(22)
F24 = make_font(24)
F28 = make_font(28)
F32 = make_font(32)
F40 = make_font(40)
F48 = make_font(48)

ZF12 = make_zh_font(12)
ZF14 = make_zh_font(14)
ZF14B = make_zh_font(14, bold=True)
ZF16 = make_zh_font(16)
ZF16B = make_zh_font(16, bold=True)
ZF18 = make_zh_font(18)
ZF20 = make_zh_font(20)
ZF22 = make_zh_font(22)
ZF24 = make_zh_font(24)


def draw_status_bar(draw, time_str="9:41"):
    """Draw iPhone-style status bar with signal, time, battery."""
    # Signal bars
    for i in range(4):
        h = 4 + i * 3
        draw.rectangle([12 + i*3, 14-h, 14 + i*3, 14], fill="#000000")
    # WiFi icon
    draw.arc([28, 12, 36, 20], 200, 340, fill="#000000", width=1)
    draw.arc([30, 14, 34, 18], 200, 340, fill="#000000", width=1)
    draw.point([32, 20], fill="#000000")
    # Time
    draw.text((170, 10), time_str, fill="#000000", font=F12)
    # Battery
    draw.rounded_rectangle([(310, 8), (332, 18)], radius=3, outline="#000000", width=1)
    draw.rectangle([(330, 10), (332, 16)], fill="#000000")
    draw.rectangle([(312, 10), (329, 16)], fill="#000000")


def draw_bottom_nav(draw, tabs, active_idx):
    """Draw iPhone bottom tab bar."""
    bar_h = 50
    bar_y = H - bar_h - 20  # leave room for home indicator
    draw.rectangle([0, bar_y, W, H - 20], fill="#f8f8f8")
    draw.line([(0, bar_y), (W, bar_y)], fill="#e0e0e0", width=1)
    
    tab_w = W // len(tabs)
    for i, (label, icon_char) in enumerate(tabs):
        x = i * tab_w + 5
        y = bar_y + 8
        color = "#007aff" if i == active_idx else "#8e8e93"
        draw.text((x, y), icon_char, fill=color, font=F14)
        draw.text((x, y + 18), label, fill=color, font=F10)
    
    # Home indicator
    draw.rounded_rectangle([(145, H - 28), (245, H - 24)], radius=4, fill="#000000")


def draw_header(draw, title, bg_color="#ffffff", text_color="#000000"):
    """Draw standard header bar."""
    draw.rectangle([0, 20, W, 56], fill=bg_color)
    draw.line([(0, 56), (W, 56)], fill="#e5e5ea", width=1)
    # Back arrow
    draw.line([(20, 32), (16, 38), (20, 44)], fill=text_color, width=2)
    # Title centered
    tw = draw.textlength(title, font=F16B)
    draw.text(((W - tw) // 2, 28), title, fill=text_color, font=F16B)


def draw_section_header(draw, y, title, subtitle="", color="#8e8e93"):
    """Section header with optional subtitle."""
    draw.text((16, y), title, fill=color, font=F13)
    if subtitle:
        draw.text((W - 16 - draw.textlength(subtitle, font=F12), y), subtitle, fill="#007aff", font=F12)


# =====================================================================
# IMAGE 03: Alipay Identity Verification (dark mode, no logo)
# =====================================================================
def gen_mobile_payment_03():
    """
    Alt: A phone screen showing the Alipay identity verification page with the passport option selected
    Dark mode, clean, no brand logos
    """
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Status bar
    draw_status_bar(draw)
    
    # Header
    draw.rectangle([0, 20, W, 56], fill='#16213e')
    draw.line([(0, 56), (W, 56)], fill='#1a1a2e', width=2)
    draw.line([(20, 32), (16, 38), (20, 44)], fill='#ffffff', width=2)
    draw.text((100, 28), "Identity Verification", fill='#ffffff', font=F16B)
    
    # Subtitle
    draw.text((20, 68), "Verify your identity to activate payments", fill='#8888aa', font=F12)
    
    # Step indicator
    sy = 92
    draw.text((20, sy), "Step 1 of 3: ID Information", fill='#ff6b35', font=F12)
    # Progress bar
    draw.rounded_rectangle([(180, sy+2), (W-20, sy+8)], radius=4, fill='#2a2a4a')
    draw.rounded_rectangle([(180, sy+2), (180 + 60*(W-200)//3, sy+8)], radius=4, fill='#ff6b35')
    
    # ID Type selection
    iy = 120
    draw.text((20, iy), "ID Type", fill='#aaaaaa', font=F13)
    
    # Passport (selected)
    draw.rounded_rectangle([(20, iy+18), (W-20, iy+62)], radius=10, fill='#16213e', outline='#ff6b35', width=2)
    draw.text((32, iy+24), "Passport", fill='#ff6b35', font=F16B)
    draw.text((32, iy+44), "Recommended for international travelers", fill='#8888aa', font=F11)
    # Radio selected
    draw.circle((W-40, iy+40), 8, outline='#ff6b35', width=2)
    draw.circle((W-40, iy+40), 4, fill='#ff6b35')
    
    # Chinese ID Card (disabled)
    cy = iy + 72
    draw.rounded_rectangle([(20, cy), (W-20, cy+44)], radius=10, fill='#1a1a2e', outline='#333355', width=1)
    draw.text((32, cy+6), "Chinese ID Card", fill='#555577', font=F14)
    draw.text((32, cy+24), "For Chinese citizens only", fill='#555577', font=F11)
    draw.circle((W-40, cy+22), 8, outline='#555577', width=1)
    
    # Foreign ID Card (disabled)
    fy = cy + 54
    draw.rounded_rectangle([(20, fy), (W-20, fy+44)], radius=10, fill='#1a1a2e', outline='#333355', width=1)
    draw.text((32, fy+6), "Foreign ID Card", fill='#555577', font=F14)
    draw.text((32, fy+24), "For certain countries", fill='#555577', font=F11)
    draw.circle((W-40, fy+22), 8, outline='#555577', width=1)
    
    # Form fields below
    fields_y = fy + 60
    fields = [
        ("Full Name", "JOHN SMITH", True),
        ("Passport Number", "E12345678", True),
        ("Nationality", "United Kingdom", True),
        ("Date of Birth", "15 January 1990", True),
        ("Expiry Date", "30 June 2028", True),
    ]
    
    for i, (label, value, editable) in enumerate(fields):
        field_y = fields_y + i * 58
        draw.text((20, field_y), label, fill='#8888aa', font=F12)
        if editable:
            draw.rounded_rectangle([(20, field_y+18), (W-20, field_y+48)], radius=8, fill='#16213e', outline='#333355', width=1)
            draw.text((30, field_y+22), value, fill='#ffffff', font=F14)
        else:
            draw.rounded_rectangle([(20, field_y+18), (W-20, field_y+48)], radius=8, fill='#1a1a2e', outline='#333355', width=1)
            draw.text((30, field_y+22), value, fill='#666688', font=F14)
    
    # Upload section
    uy = fields_y + 58 * len(fields) + 10
    draw.text((20, uy), "Upload Passport Photo", fill='#8888aa', font=F13)
    draw.rounded_rectangle([(20, uy+16), (W-20, uy+90)], radius=10, fill='#16213e', outline='#ff6b35', width=2)
    # Upload icon
    draw.line([(W//2-10, uy+30), (W//2+10, uy+30)], fill='#ff6b35', width=2)
    draw.line([(W//2, uy+22), (W//2, uy+38)], fill='#ff6b35', width=2)
    draw.text((W//2 - 60, uy+48), "Tap to upload", fill='#ff6b35', font=F14)
    draw.text((W//2 - 45, uy+68), "JPG or PNG, max 10MB", fill='#666688', font=F11)
    
    # Warning
    wy = uy + 100
    draw.text((20, wy), "Ensure all details match your passport exactly.", fill='#ff6b35', font=F11)
    
    # Submit button
    btn_y = wy + 30
    draw.rounded_rectangle([(20, btn_y), (W-20, btn_y+48)], radius=24, fill='#ff6b35')
    draw.text((130, btn_y+14), "Continue", fill='#ffffff', font=F18B)
    
    # Bottom nav
    draw_bottom_nav(draw, [("Home", "🏠"), ("Finance", "💰"), ("Messages", "💬"), ("Me", "👤")], 3)
    
    img.save(os.path.join(IMAGES_DIR, "mobile-payment-03-alipay-identity-verification.jpg"), "JPEG", quality=92)
    print("✓ Generated mobile-payment-03-alipay-identity-verification.jpg")


# =====================================================================
# IMAGE 05: WeChat Services page (green theme, no logo)
# =====================================================================
def gen_mobile_payment_05():
    """
    Alt: WeChat interface showing the Services section with WeChat Pay icon and balance display
    Clean green theme, no brand logos
    """
    img = Image.new('RGB', (W, H), '#f2f2f2')
    draw = ImageDraw.Draw(img)
    
    # Status bar
    draw_status_bar(draw)
    
    # Header - green
    draw.rectangle([0, 20, W, 56], fill='#07c160')
    draw.line([(0, 56), (W, 56)], fill='#06a852', width=2)
    draw.line([(20, 32), (16, 38), (20, 44)], fill='#ffffff', width=2)
    draw.text((100, 28), "Services", fill='#ffffff', font=F16B)
    
    # Search bar
    draw.rounded_rectangle([(20, 64), (W-20, 94)], radius=20, fill='#ffffff')
    draw.text((40, 70), "Search", fill='#cccccc', font=F13)
    
    # Balance card
    card_y = 108
    draw.rounded_rectangle([(20, card_y), (W-20, card_y+80)], radius=12, fill='#07c160')
    draw.text((36, card_y+14), "WeChat Pay", fill='rgba(255,255,255,0.85)', font=F14)
    draw.text((36, card_y+36), "¥ 1,286.50", fill='#ffffff', font=F32)
    draw.text((36, card_y+60), "Visa •••• 4632", fill='rgba(255,255,255,0.75)', font=F12)
    
    # Quick actions row
    qa_y = card_y + 100
    qa_items = [
        ("Transfer", "↗"),
        ("Pay", "¥"),
        ("Collect", "←"),
        ("Cards", "💳"),
    ]
    for i, (label, icon) in enumerate(qa_items):
        x = 20 + i * 90
        draw.text((x + 18, qa_y), icon, fill='#333333', font=F20)
        draw.text((x + 10, qa_y + 24), label, fill='#555555', font=F11)
    
    # Section header
    sh_y = qa_y + 52
    draw_section_header(draw, sh_y, "Common Services")
    
    # Service grid
    sg_y = sh_y + 22
    services = [
        ("Flight & Hotel", "✈"),
        ("Food Delivery", "🍜"),
        ("Ride Hailing", "🚗"),
        ("Movie Tickets", "🎬"),
        ("Utilities", "💡"),
        ("Transit", "🚇"),
        ("Healthcare", "🏥"),
        ("Shopping", "🛒"),
    ]
    
    for i, (label, icon) in enumerate(services):
        col = i % 4
        row = i // 4
        sx = 20 + col * 95
        sy = sg_y + row * 72
        
        draw.rounded_rectangle([(sx, sy), (sx+65, sy+65)], radius=12, fill='#ffffff')
        draw.text((sx+20, sy+12), icon, fill='#07c160', font=F22)
        draw.text((sx+5, sy+44), label, fill='#333333', font=F10)
    
    # Promo banner
    promo_y = sg_y + 152
    draw.rounded_rectangle([(20, promo_y), (W-20, promo_y+80)], radius=10, fill='#1a1a2e')
    draw.text((32, promo_y+16), "Earn Rewards", fill='#07c160', font=F18B)
    draw.text((32, promo_y+40), "Get cashback on every payment", fill='#aaaaaa', font=F12)
    draw.text((32, promo_y+58), "Learn More >", fill='#07c160', font=F12)
    
    # My Orders
    mo_y = promo_y + 100
    draw.line([(20, mo_y), (W-20, mo_y)], fill='#e5e5ea', width=1)
    draw_section_header(draw, mo_y + 6, "My Orders", "All >", color='#333333')
    
    order_tabs_y = mo_y + 30
    order_tabs = [("Pending", True), ("Shipping", False), ("Received", False), ("Reviews", False)]
    for i, (label, active) in enumerate(order_tabs):
        x = 20 + i * 70
        color = '#07c160' if active else '#8e8e93'
        draw.text((x, order_tabs_y), label, fill=color, font=F12)
        if active:
            draw.line([(x, order_tabs_y+14), (x+draw.textlength(label, font=F12)+4, order_tabs_y+14)], fill='#07c160', width=2)
    
    # Bottom nav
    draw_bottom_nav(draw, [("Chats", "💬"), ("Contacts", "👥"), ("Discover", "🔍"), ("Me", "👤")], 0)
    
    img.save(os.path.join(IMAGES_DIR, "mobile-payment-05-wechat-pay-interface.jpg"), "JPEG", quality=92)
    print("✓ Generated mobile-payment-05-wechat-pay-interface.jpg")


# =====================================================================
# IMAGE 08: WeChat Wallet home (replaces Bank of China ATM)
# =====================================================================
def gen_mobile_payment_08():
    """
    Alt: WeChat Wallet home screen showing the current balance, transaction history, 
         and core service buttons like Transfer and Card Linking
    Realistic wallet interface, no ATM, no Bank of China logo
    """
    img = Image.new('RGB', (W, H), '#ededed')
    draw = ImageDraw.Draw(img)
    
    # Status bar
    draw_status_bar(draw)
    
    # Header
    draw.rectangle([0, 20, W, 56], fill='#ffffff')
    draw.line([(0, 56), (W, 56)], fill='#e5e5ea', width=1)
    draw.line([(20, 32), (16, 38), (20, 44)], fill='#333333', width=2)
    draw.text((100, 28), "Wallet", fill='#000000', font=F16B)
    # Scan icon
    draw.rectangle([(340, 28), (356, 44)], outline='#333333', width=2)
    draw.line([(348, 28), (348, 44)], fill='#333333', width=2)
    draw.line([(340, 36), (356, 36)], fill='#333333', width=2)
    
    # Green balance card
    bc_y = 68
    draw.rounded_rectangle([(20, bc_y), (W-20, bc_y+110)], radius=14, fill='#07c160')
    draw.text((32, bc_y+14), "Balance", fill='rgba(255,255,255,0.8)', font=F13)
    draw.text((32, bc_y+36), "¥ 1,286.50", fill='#ffffff', font=F36)
    draw.text((32, bc_y+72), "Tap to view details", fill='rgba(255,255,255,0.6)', font=F11)
    
    # Card chips
    cards_y = bc_y + 125
    draw.text((20, cards_y), "Linked Cards", fill='#333333', font=F14B)
    draw.text((W-100, cards_y), "Manage >", fill='#07c160', font=F12)
    
    # Card 1 - Visa
    c1y = cards_y + 18
    draw.rounded_rectangle([(20, c1y), (W-20, c1y+60)], radius=10, fill='#ffffff')
    draw.text((32, c1y+14), "Visa", fill='#1a1f71', font=F16B)
    draw.text((32, c1y+36), "•••• 4632", fill='#666666', font=F13)
    draw.text((W-100, c1y+36), "Default", fill='#07c160', font=F11)
    
    # Card 2 - Mastercard
    c2y = c1y + 70
    draw.rounded_rectangle([(20, c2y), (W-20, c2y+60)], radius=10, fill='#ffffff')
    draw.text((32, c2y+14), "Mastercard", fill='#eb001b', font=F14B)
    draw.text((32, c2y+36), "•••• 8871", fill='#666666', font=F13)
    
    # Quick actions
    qa_y = c2y + 80
    draw.line([(20, qa_y), (W-20, qa_y)], fill='#e5e5ea', width=1)
    
    qa_items = [
        ("Transfer", "↑↓"),
        ("Pay", "¥"),
        ("Receive", "↓↑"),
        ("Cards", "💳"),
        ("Top Up", "+"),
        ("Wealth", "📈"),
    ]
    
    for i, (label, icon) in enumerate(qa_items):
        x = 16 + i * 63
        y = qa_y + 12
        draw.text((x + 14, y), icon, fill='#07c160', font=F18)
        draw.text((x + 8, y + 22), label, fill='#555555', font=F10)
    
    # Transaction history
    tx_y = qa_y + 65
    draw.text((20, tx_y), "Recent Transactions", fill='#333333', font=F14B)
    draw.text((W-80, tx_y), "See All >", fill='#07c160', font=F12)
    
    transactions = [
        ("Noodle King", "¥ -28.00", "Today 12:30 PM"),
        ("Starbucks", "¥ -42.00", "Today 10:15 AM"),
        ("Didi Ride", "¥ -28.60", "Yesterday"),
        ("FamilyMart", "¥ -16.50", "Yesterday"),
        ("Top Up", "¥ +500.00", "Jun 19"),
    ]
    
    for i, (merchant, amount, date) in enumerate(transactions):
        ty = tx_y + 28 + i * 55
        draw.line([(20, ty), (W-20, ty)], fill='#f0f0f0', width=1)
        
        # Icon circle
        colors = ['#ff6b35', '#07c160', '#4a90d9', '#e74c3c', '#f39c12']
        draw.circle((38, ty+14), 14, fill=colors[i % len(colors)])
        draw.text((30, ty+8), "💰", fill='#ffffff', font=F14)
        
        draw.text((62, ty+4), merchant, fill='#333333', font=F13)
        draw.text((62, ty+22), date, fill='#999999', font=F10)
        
        amt_color = '#e74c3c' if '-' in amount else '#07c160'
        draw.text((W-20 - draw.textlength(amount, font=F14B), ty+4), amount, fill=amt_color, font=F14B)
    
    # Bottom nav
    draw_bottom_nav(draw, [("Chats", "💬"), ("Contacts", "👥"), ("Discover", "🔍"), ("Me", "👤")], 3)
    
    img.save(os.path.join(IMAGES_DIR, "mobile-payment-08-bank-of-china-atm.jpg"), "JPEG", quality=92)
    print("✓ Generated mobile-payment-08-bank-of-china-atm.jpg")


if __name__ == "__main__":
    gen_mobile_payment_03()
    gen_mobile_payment_05()
    gen_mobile_payment_08()
    print("\nAll 3 images regenerated successfully!")
