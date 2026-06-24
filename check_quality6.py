files = [
    ('EA-01', r'E:\项目库\china-travel-website\articles\essential-apps-for-traveling-in-china\images\essential-apps-01-home-screen.jpg'),
    ('MP-01', r'E:\项目库\china-travel-website\articles\mobile-payment-in-china\images\01-street-food-market.jpg'),
]

for name, fp in files:
    with open(fp, 'rb') as f:
        data = f.read()
    
    # Find DQT positions
    pos = 0
    while pos < len(data):
        if data[pos] == 0xFF and data[pos+1] == 0xDB:
            seg_len = (data[pos+2] << 8) | data[pos+3]
            seg = data[pos+4:pos+seg_len]
            print(name + ': DQT segment at pos=' + str(pos) + ' len=' + str(seg_len))
            print('  first 20 bytes of DQT payload: ' + str(list(seg[:20])))
        pos += 1
