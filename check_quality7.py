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
    qt_num = 0
    while pos < len(data):
        if data[pos] == 0xFF and data[pos+1] == 0xDB:
            seg_len = (data[pos+2] << 8) | data[pos+3]
            seg = data[pos+4:pos+seg_len]
            qt_precision = (seg[0] >> 4) & 0x0F
            qt_id = seg[0] & 0x0F
            if qt_precision == 0:
                qt_table = list(seg[2:66])
                avg_val = sum(qt_table) / len(qt_table)
                print(name + ': QT#' + str(qt_num) + ' id=' + str(qt_id) + ' avg=' + str(round(avg_val, 2)))
                print('  ' + str(qt_table))
                qt_num += 1
        pos += 1
