import sys, os, glob
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(os.path.join(src, 'etelaeieImage*'))):
    if f.endswith('.pdf'): continue
    im = Image.open(f)
    w, h = im.size
    r = w / h
    if abs(w/h - 1667/938) < 0.05:   # new template: map + info panels
        box = (int(w*0.458), int(h*0.03), w, int(h*0.88))
        im = im.crop(box)
    im.convert('RGB').save(os.path.join(dst, os.path.basename(f).rsplit('.',1)[0] + '.jpg'), quality=88)
    print(os.path.basename(f), w, h)
