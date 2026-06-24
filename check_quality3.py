from PIL import Image
import io

files = [
    ('EA-01', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-01-home-screen.jpg'),
    ('EA-02', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-02-maps-street-scene.jpg'),
    ('EA-04', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-04-translation-restaurant-scene.jpg'),
    ('MP-01', r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\01-street-food-market.jpg'),
    ('MP-04', r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\04-bank-of-china-atm.jpg'),
]

for name, fp in files:
    with open(fp, 'rb') as f:
        data = f.read()
    
    # Find DQT segments
    pos = 0
    all_qt = []
    while pos < len(data) - 1:
        if data[pos] == 0xFF:
            marker = data[pos+1]
            if marker == 0xFF:
                pos += 2
                continue
            elif marker == 0xDB:
                seg_len = (data[pos+2] << 8) | data[pos+3]
                seg_data = data[pos+4:pos+seg_len]
                i = 0
                while i < len(seg_data):
                    if i + 1 >= len(seg_data):
                        break
                    qt_info = seg_data[i]
                    qt_precision = (qt_info >> 4) & 0x0F
                    if qt_precision == 0 and i + 67 <= len(seg_data):
                        qt_table = list(seg_data[i+2:i+66])
                        all_qt.extend(qt_table)
                        break
                    i += seg_data[i] + 1 if seg_data[i] < 256 else len(seg_data) - i
                pos += seg_len
                continue
            elif marker == 0xD9:
                break
            elif marker == 0xD8:
                pos += 2
                continue
            else:
                if pos + 4 <= len(data):
                    seg_len = (data[pos+2] << 8) | data[pos+3]
                    if seg_len < 2:
                        pos += 1
                        continue
                    pos += seg_len
                else:
                    break
        else:
            pos += 1
    
    if all_qt:
        avg_qt = sum(all_qt) / len(all_qt)
        print(f'{name}: avg_quant={avg_qt:.1f}, num_coeffs={len(all_qt)}, first10={all_qt[:10]}')
    else:
        print(f'{name}: NO QT TABLES FOUND')
