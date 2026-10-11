"""List sketch/notice image URLs of tracked listings that are not downloaded yet (for scripts/fetch_imgs.js).

  .venv/bin/python -I scripts/img_urls.py > data/img_urls_new.txt
"""
import json
import os
import re

rows = json.load(open('data/residential_listings.json', encoding='utf-8'))
have = set(os.listdir('data/img'))
urls = []
for r in rows:
    for u in (r.get('koroki'),):
        if not u:
            continue
        name = u.split('/')[-1]
        if name not in have and re.search(r'(koroki|etelaeie)Image\d+', name):
            urls.append(u)
for u in dict.fromkeys(urls):
    print(u)
