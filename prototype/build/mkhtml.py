"""Generates app/farmer.html and app/consumer.html from app/index.html (APP flag + crop catalogue)."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "app", "index.html"), encoding="utf8").read()
crops = open(os.path.join(ROOT, "data", "crops.json"), encoding="utf8").read()
for app, out in (("buyer", "consumer.html"), ("farmer", "farmer.html")):
    s = src.replace('"__APP__"', '"%s"' % app).replace("__CROPS__", crops if app == "farmer" else "[]")
    open(os.path.join(ROOT, "app", out), "w", encoding="utf8").write(s)
    print(out, len(s))
