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
    
    pos = 0
    while pos < len(data) - 4:
        if data[pos] == 0xFF and data[pos+1] == 0xDB:
            seg_len = (data[pos+2] << 8) | data[pos+3]
            seg = data[pos+4:pos+seg_len]
            i = 0
            while i < len(seg):
                if i + 1 >= len(seg):
                    break
                qt_byte = seg[i]
                qt_precision = (qt_byte >> 4) & 0x0F
                qt_id = qt_byte & 0x0F
                if qt_precision == 0 and i + 67 <= len(seg):
                    qt_table = seg[i+2:i+66]
                    avg_val = sum(qt_table) / len(qt_table)
                    print(name + ': QT id=' + str(qt_id) + ' avg=' + str(round(avg_val, 1)) + ' first8=' + str(list(qt_table[:8])))
                i = i + seg[i] + 1
            pos = pos + seg_len
        else:
            pos = pos + 1
