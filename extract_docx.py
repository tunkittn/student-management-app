import zipfile
import os
import xml.etree.ElementTree as ET

path = r'D:\Source capcut\btap\tieuluancuoiki.docx'
print('exists', os.path.exists(path))
with zipfile.ZipFile(path) as z:
    print('names', z.namelist())
    data = z.read('word/document.xml')
    root = ET.fromstring(data)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    texts = []
    for p in root.findall('.//w:p', ns):
        paras = []
        for t in p.findall('.//w:t', ns):
            if t.text:
                paras.append(t.text)
        if paras:
            texts.append(''.join(paras))
    print('\n'.join(texts[:200]))
