from zipfile import ZipFile
from pathlib import Path

pptx = Path("talk.pptx")
out = Path("images_out")
out.mkdir(exist_ok=True)

with ZipFile(pptx) as z:
    for name in z.namelist():
        if name.startswith("ppt/media/"):
            z.extract(name, out)

print("Done. See images in images_out/ppt/media/")