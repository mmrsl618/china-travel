from PIL import Image
import os

files = [
    'E:/项目库/china-travel-website/images/mobile-payment-05-wechat-pay-interface.jpg',
    'E:/项目库/china-travel-website/images/mobile-payment-08-bank-of-china-atm.jpg',
]
for f in files:
    img = Image.open(f)
    orig_size_kb = os.path.getsize(f) / 1024
    img.save(f, optimize=True, quality=85)
    new_size_kb = os.path.getsize(f) / 1024
    print(f'{os.path.basename(f)}: {orig_size_kb:.0f}KB -> {new_size_kb:.0f}KB')
