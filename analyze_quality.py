from PIL import Image
import os, glob

ea_files = sorted(glob.glob(r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\*.jpg'))
mp_files = sorted(glob.glob(r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\*.jpg'))

def get_jpeg_quality(filepath):
    """Read JPEG file header to extract quality factor."""
    with open(filepath, 'rb') as f:
        data = f.read()
    # JPEG SOF (Start of Frame) marker is 0xFFC0 (baseline) or 0xFFC2 (progressive)
    # Find quality factor in DHT segment (0xFFC4) - actually quality is in SOS/SOF
    # Quality factor is stored in every MCU-related segment
    # Simplest: find 0xFFDA (SOS) and look back for quantization table precision
    # Actually, quality is encoded in the quantization tables
    # Let's scan for JPEG segments and find quantization table length
    pos = 0
    while pos < len(data) - 1:
        if data[pos] == 0xFF:
            marker = data[pos+1]
            if marker == 0xD8:  # SOI
                pos += 2
                continue
            elif marker == 0xD9:  # EOI
                break
            elif 0xC0 <= marker <= 0xCF and marker != 0xC4:  # SOF markers
                length = int.from_bytes(data[pos+2:pos+4], 'big')
                quality = data[pos+5]  # Precision byte (usually 8)
                # The actual quality factor is in the quantization table segment
                pos += length
                continue
            elif marker == 0xC4:  # DHT (defines quantization tables)
                # Skip to find quantization table
                seg_start = pos
                length = int.from_bytes(data[pos+2:pos+4], 'big')
                seg_data = data[pos+4:pos+length]
                # Search for quantization table info
                for i in range(len(seg_data) - 1):
                    if seg_data[i] == 0xFF and seg_data[i+1] == 0xDA:
                        break
                    if i + 9 < len(seg_data):
                        qt_type = seg_data[i]
                        qt_precision = seg_data[i+1]
                        qt_len = int.from_bytes(seg_data[i+2:i+4], 'big')
                        if qt_len > 0 and qt_len < 1000:
                            # Quantization table data starts at i+4
                            qt_data = seg_data[i+4:i+4+qt_len-2]
                            if len(qt_data) >= 64:
                                # Approximate quality from DC coefficients
                                dc_avg = sum(abs(x) for x in qt_data[:64]) / 64
                                if dc_avg > 0:
                                    # Higher avg = lower quality (more compression)
                                    est_quality = max(1, min(100, int(255 / dc_avg * 10)))
                                    return est_quality
                pos += length
                continue
            elif marker == 0xFE:  # COM
                length = int.from_bytes(data[pos+2:pos+4], 'big')
                pos += length
                continue
            elif marker == 0xDD:  # DQT
                length = int.from_bytes(data[pos+2:pos+4], 'big')
                seg_data = data[pos+4:pos+length]
                for i in range(0, len(seg_data) - 65, 1):
                    if i + 66 <= len(seg_data):
                        qt_type = seg_data[i]
                        qt_precision = seg_data[i+1]
                        qt_data = seg_data[i+2:i+66]
                        if qt_precision == 0:  # 8-bit precision
                            dc_avg = sum(abs(x - 128 if x > 128 else x) for x in qt_data) / 64
                            # Better estimation: average of quantization values
                            q_avg = sum(qt_data) / 64
                            if q_avg > 0:
                                # Standard JPEG quality mapping
                                est = int(100 - (q_avg - 10) / 200 * 100)
                                est = max(1, min(100, est))
                                return est
                pos += length
                continue
            elif marker == 0x00:  # stuffed byte
                pos += 1
                continue
            else:
                if pos + 2 < len(data):
                    length = int.from_bytes(data[pos+2:pos+4], 'big')
                    if length < 2 or length > 65535:
                        pos += 1
                        continue
                    pos += length
                else:
                    break
        else:
            pos += 1
    return None

print('=== Essential Apps - Quality Analysis ===')
for f in ea_files:
    img = Image.open(f)
    quality = get_jpeg_quality(f)
    sz = os.path.getsize(f)/1024
    print(f'{os.path.basename(f)}: {img.size} size={sz:.1f}KB quality≈{quality}')
    img.close()

print()
print('=== Mobile Payment - Quality Analysis ===')
for f in mp_files:
    img = Image.open(f)
    quality = get_jpeg_quality(f)
    sz = os.path.getsize(f)/1024
    print(f'{os.path.basename(f)}: {img.size} size={sz:.1f}KB quality≈{quality}')
    img.close()
