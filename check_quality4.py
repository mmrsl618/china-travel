# Quick JPEG quality extraction

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
    
    # Scan for 0xFFDB (DQT) segments
    dqt_positions = []
    pos = 0
    while pos < len(data) - 4:
        if data[pos] == 0xFF and data[pos+1] == 0xDB:
            seg_len = (data[pos+2] << 8) | data[pos+3]
            dqt_positions.append((pos, seg_len))
        pos += 1
    
    print(f'\n{name}: {len(dqt_positions)} DQT segments found')
    for dqt_pos, dqt_len in dqt_positions:
        seg = data[dqt_pos+4:dqt_pos+dqt_len]
        # Parse quantization tables
        i = 0
        while i + 1 < len(seg):
            qt_byte = seg[i]
            qt_precision = (qt_byte >> 4) & 0x0F
            qt_id = qt_byte & 0x0F
            if qt_precision == 0 and i + 67 <= len(seg):
                qt_table = seg[i+2:i+66]
                avg_val = sum(qt_table) / len(qt_table)
                max_val = max(qt_table)
                min_val = min(qt_table)
                print(f'  QT id={qt_id}: avg={avg_val:.1f} max={max_val} min={min_val}')
                print(f'    values: {list(qt_table[:16])} ... {list(qt_table[64:])}')
            i += seg[i] + 1 if seg[i] < 256 else len(seg) - i
