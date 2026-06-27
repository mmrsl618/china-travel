import urllib.request, xml.etree.ElementTree as ET

url = 'https://visitchinatips.com/sitemap.xml'
data = urllib.request.urlopen(url).read().decode('utf-8')
print(f'Bytes: {len(data)}')

root = ET.fromstring(data)
ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
urls = root.findall(f'{ns}url')
print(f'URLs: {len(urls)}')

for u in urls:
    loc = u.find(f'{ns}loc').text
    pri = u.find(f'{ns}priority').text
    freq = u.find(f'{ns}changefreq').text
    print(f'  {pri} {freq:8s} {loc}')

print('XML valid')
