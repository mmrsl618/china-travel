from PIL import Image
import io, struct

def get_jpeg_quality_simple(filepath):
    """Extract JPEG quality from quantization tables."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find DQT segments (0xFFD8 is SOI, 0xFFD9 is EOI)
    # DQT = 0xFFDB
    pos = 0
    qt_values = []
    while pos < len(data) - 1:
        if data[pos] == 0xFF:
            marker = data[pos+1]
            if marker == 0xFF:  # stuffed byte
                pos += 2
                continue
            elif marker == 0xDB:  # DQT
                if pos + 4 <= len(data):
                    seg_len = (data[pos+2] << 8) | data[pos+3]
                    seg_end = pos + seg_len
                    seg_data = data[pos+4:seg_end]
                    i = 0
                    while i + 1 < len(seg_data):
                        qt_info = seg_data[i]
                        qt_precision = (qt_info >> 4) & 0x0F
                        qt_id = qt_info & 0x0F
                        if qt_precision == 0 and i + 67 <= len(seg_data):
                            qt_table = list(seg_data[i+2:i+66])
                            qt_values.extend(qt_table)
                        i += seg_data[i] + 1 if i < len(seg_data) else len(seg_data)
                    pos = seg_end
                    continue
            elif marker == 0xC0 or marker == 0xC1:  # SOF0/SOF1
                if pos + 7 <= len(data):
                    precision = data[pos+5]
                    height = (data[pos+6] << 8) | data[pos+7]
                    width_data_pos = pos + 8
                    # Skip to find width
                    sof_seg_len = (data[pos+2] << 8) | data[pos+3]
                    pos += sof_seg_len
                    continue
            elif marker == 0xD9:  # EOI
                break
            elif marker == 0xD8:  # SOI
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
    
    if qt_values:
        avg_qt = sum(qt_values) / len(qt_values)
        # Standard approximation: quality ≈ 100 - (avg_qt - 5) / 1.99
        # Or simpler: map 0-255 quantization to quality
        est_quality = max(1, min(100, int(100 - (avg_qt - 5) * 0.5)))
        return est_quality, avg_qt, qt_values[:10]
    return None, None, None

files = [
    ('EA-01', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-01-home-screen.jpg'),
    ('EA-02', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-02-maps-street-scene.jpg'),
    ('MP-01', r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\01-street-food-market.jpg'),
    ('MP-04', r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\04-bank-of-china-atm.jpg'),
]

for name, fp in files:
    q, avg, sample = get_jpeg_quality_simple(fp)
    print(f'{name}: quality≈{q}, avg_qt={avg:.1f}, qt_sample={sample}')
