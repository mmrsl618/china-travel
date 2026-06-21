import sys
sys.path.insert(0, r'D:\Qwenpaw\.qwenpaw\workspaces\meigong')
from agnes_image_gen import generate_image

# 01: 支付宝扫码付款界面
generate_image(
    'A realistic smartphone screen showing a mobile payment QR code scanning interface at a Chinese street food market stall. The phone displays a generic payment app with a scan-to-pay screen, showing a QR code being scanned. Photorealistic style, real phone screen capture aesthetic, no watermarks, no brand logos or text.',
    r'E:\项目库\china-travel-website\images\mobile-payment-01-street-food-market.png'
)
print('=== 01 DONE ===')

# 03: 支付宝实名认证界面
generate_image(
    'A realistic smartphone screen showing a mobile payment identity verification screen. The phone displays a generic KYC verification interface with ID card upload area, facial recognition prompt, and personal info fields. Clean modern UI design. Photorealistic style, real phone screen capture aesthetic, no watermarks, no brand logos or text.',
    r'E:\项目库\china-travel-website\images\mobile-payment-03-alipay-identity-verification.jpg'
)
print('=== 03 DONE ===')

# 05: 微信支付界面
generate_image(
    'A realistic smartphone screen showing a mobile payment confirmation interface. The phone displays a generic payment app with order details, amount display, and pay button. Clean modern UI. Photorealistic style, real phone screen capture aesthetic, no watermarks, no brand logos or text.',
    r'E:\项目库\china-travel-website\images\mobile-payment-05-wechat-pay-interface.jpg'
)
print('=== 05 DONE ===')

# 08: 微信钱包首页
generate_image(
    'A realistic smartphone screen showing a mobile wallet home screen. The phone displays a generic digital wallet app homepage with balance overview, transfer money button, QR code scan button, and payment services grid. Clean modern UI design. Photorealistic style, real phone screen capture aesthetic, no watermarks, no brand logos or text.',
    r'E:\项目库\china-travel-website\images\mobile-payment-08-bank-of-china-atm.jpg'
)
print('=== 08 DONE ===')

print('ALL IMAGES GENERATED SUCCESSFULLY')
