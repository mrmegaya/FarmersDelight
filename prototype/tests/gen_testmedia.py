"""Creates the test photos and videos used by the tests (needs Pillow, numpy and ffmpeg)."""
import os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media"); os.makedirs(D, exist_ok=True)
for i, (c1, c2) in enumerate([((200, 40, 30), (90, 140, 50)), ((180, 120, 60), (60, 100, 30)), ((230, 90, 60), (40, 80, 20)), ((150, 60, 170), (60, 30, 80))]):
    im = Image.new("RGB", (3000, 2000), c2); d = ImageDraw.Draw(im); random.seed(i)
    for _ in range(60):
        x, y, r = random.randint(0, 3000), random.randint(0, 2000), random.randint(60, 140); d.ellipse([x - r, y - r, x + r, y + r], fill=c1)
    ex = Image.Exif(); ex[0x010F] = "TestPhone"; ex[0x8825] = {1: "N", 2: (11.0, 1.0, 0.0), 3: "E", 4: (76.0, 57.0, 0.0)}   # GPS that must be stripped
    im.save(os.path.join(D, f"photo{i+1}.jpg"), quality=90, exif=ex)
# 50 MP photos like the Redmi 13 Pro+ camera (8160x6120), landscape and portrait
Image.fromarray((np.random.default_rng(1).random((6120, 8160, 3)) * 255).astype("uint8")).save(os.path.join(D, "big50mp.jpg"), quality=85)
Image.fromarray((np.random.default_rng(2).random((8160, 6120, 3)) * 255).astype("uint8")).save(os.path.join(D, "big50mp_portrait.jpg"), quality=85)
open(os.path.join(D, "fake.heic"), "wb").write(b"\x00\x00\x00\x18ftypheic" + b"\x00" * 500)
run = lambda *a: subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *a], check=True)
run("-f", "lavfi", "-i", "testsrc=duration=24:size=1920x1080:rate=30", "-f", "lavfi", "-i", "sine=frequency=440:duration=24", "-shortest", "-c:v", "libvpx", "-b:v", "2M", "-c:a", "libvorbis", os.path.join(D, "long24.webm"))
run("-f", "lavfi", "-i", "testsrc2=duration=6:size=1280x720:rate=30", "-c:v", "libvpx", "-b:v", "1M", os.path.join(D, "short6.webm"))
print("test media in", D)
