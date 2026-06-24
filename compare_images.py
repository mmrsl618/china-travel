from PIL import Image
import os, glob

ea_files = sorted(glob.glob(r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\*.jpg'))
mp_files = sorted(glob.glob(r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\*.jpg'))

print('=== Essential Apps ===')
for f in ea_files:
    img = Image.open(f)
    sz = os.path.getsize(f)/1024
    print(f'{os.path.basename(f)}: {img.size} size={sz:.1f}KB')
    img.close()

print()
print('=== Mobile Payment (previous high quality) ===')
for f in mp_files:
    img = Image.open(f)
    sz = os.path.getsize(f)/1024
    print(f'{os.path.basename(f)}: {img.size} size={sz:.1f}KB')
    img.close()
