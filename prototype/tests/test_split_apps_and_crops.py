"""Tests for the split apps: consumer smoke test + farmer crop picker / unlisted items / selling flow."""
import os
from playwright.sync_api import sync_playwright
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))        # prototype/
APPDIR = os.path.join(ROOT, "app")                                        # run build/mkhtml.py first
MEDIA = os.path.join(ROOT, "tests", "media")                              # run tests/gen_testmedia.py first
SHOTS = os.path.join(ROOT, "tests", "screenshots")

SH = SHOTS
os.makedirs(SH, exist_ok=True)
errors = []
CLOCK = "(()=>{const real=Date.now.bind(Date);let off=0;Date.now=()=>real()+off;window.__adv=ms=>{off+=ms;};})();"


def page(pw, url):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.add_init_script(CLOCK)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(url[-14:] + " pageerror: " + str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(url[-14:] + " console: " + m.text))
    pg.goto(url)
    return b, pg


def helpers(pg):
    def shot(n, full=False):
        pg.wait_for_timeout(250); pg.evaluate("document.getElementById('toast').className=''"); pg.wait_for_timeout(260)
        pg.screenshot(path=f"{SH}/{n}.png", full_page=full)
    def adv(ms):
        pg.evaluate(f"__adv({ms})"); pg.wait_for_timeout(1300)
    def login():
        pg.click("text=Continue"); pg.fill("#nm", "Mega Pillai"); pg.fill("#ph", "9876543210")
        pg.click("text=Send OTP"); pg.fill("#otp", "1234"); pg.click("text=Verify and continue")
    return shot, adv, login


with sync_playwright() as pw:
    # ---------------- consumer app
    b, pg = page(pw, "file://" + APPDIR + "/consumer.html")
    shot, adv, login = helpers(pg)
    shot("c01_welcome"); login()
    assert "#explore" in pg.url, pg.url
    shot("c02_explore")
    pg.click(".nav >> text=Profile"); shot("c03_profile")
    assert pg.locator("text=I'm using the app as").count() == 0, "role switch should be gone"
    pg.click(".nav >> text=Explore"); pg.click(".seg >> text=List")
    pg.locator(".lc", has_text="Tomato").first.click(); pg.click("text=Place order"); adv(8000)
    assert pg.locator("text=Call").count() >= 1
    b.close()

    # ---------------- farmer app
    b, pg = page(pw, "file://" + APPDIR + "/farmer.html")
    shot, adv, login = helpers(pg)
    shot("f01_welcome"); login()
    assert "#farm-setup" in pg.url, pg.url
    pg.fill("#fv", "Thondamuthur"); pg.click("#pm", position={"x": 260, "y": 110}); pg.click("text=Save farm")
    shot("f02_home")
    assert pg.locator(".nav >> text=Explore").count() == 0
    pg.click(".nav >> text=Add")
    pg.wait_for_selector(".vgrid .vg"); tiles = pg.locator(".vgrid .vg")
    assert tiles.count() == 20, tiles.count()
    assert tiles.nth(18).inner_text().strip().endswith("Others"), tiles.nth(18).inner_text()
    assert tiles.nth(19).inner_text().strip().endswith("Unlisted"), tiles.nth(19).inner_text()
    # 4 columns x 5 rows
    boxes = [tiles.nth(i).bounding_box() for i in range(20)]
    cols = sorted(set(round(bx["x"]) for bx in boxes)); rows = sorted(set(round(bx["y"]) for bx in boxes))
    assert len(cols) == 4 and len(rows) == 5, (cols, rows)
    shot("f03_add_grid")
    # Others -> catalogue
    pg.click(".vg >> text=Others")
    assert "#f-crops" in pg.url
    cq = pg.locator("#cq").bounding_box(); assert cq["y"] < 80, cq
    shot("f04_catalogue")
    pg.wait_for_selector("#cg .vg"); assert pg.locator("#cg .vg").count() == 13
    pg.click("#cg .vg >> text=Vegetables"); pg.wait_for_timeout(600)
    assert pg.locator(".crow").count() == 45, pg.locator(".crow").count()
    assert pg.locator("text=Gourds and cucurbits").count() == 1
    shot("f05_vegetables")
    pg.click("#cg .vg >> text=Flowers"); pg.wait_for_timeout(600); shot("f06_flowers")
    pg.fill("#cq", "millet"); pg.wait_for_timeout(200)
    n = pg.locator(".crow").count(); assert n == 8, n
    shot("f07_search")
    pg.locator(".crow", has_text="Foxtail millet").click()
    assert "#f-add" in pg.url, pg.url
    assert pg.locator("text=Foxtail millet (Thinai)").count() >= 1
    shot("f08_selected_other")
    # Unlisted: add 5, 6th blocked
    names = ["Country chicken eggs", "Honey", "Cow milk", "Palm jaggery", "Banana leaf"]
    emos = ["🥚", "🍯", "🥛", "🌱", "🌿"]
    for nm, e in zip(names, emos):
        pg.click(".vg >> text=Unlisted"); pg.fill("#un", nm); pg.click(f".emo >> text={e}")
        pg.fill("#un", nm)  # re-render of sheet keeps text but be safe
        if nm == "Honey": shot("f09_unlisted_sheet")
        pg.click("text=Add and select"); pg.wait_for_timeout(150)
    pg.click(".vg >> text=Unlisted")
    assert pg.locator("text=5 / 5").count() == 1
    assert pg.locator("#un").count() == 0, "add form must be hidden at 5 items"
    shot("f10_unlisted_full")
    # duplicate check after removing one
    pg.locator(".sheet .item", has_text="Banana leaf").locator("[aria-label=Remove]").click()
    assert pg.locator("text=4 / 5").count() == 1
    pg.fill("#un", "honey"); pg.click("text=Add and select")
    assert pg.locator("text=4 / 5").count() == 1, "duplicate should be refused"
    pg.locator(".sheet .item", has_text="Cow milk").locator("text=Select").click()
    assert pg.locator("text=Cow milk").count() >= 1
    pg.fill("#d_qty", "20"); pg.select_option("#d_unit", "piece") if False else None
    pg.fill("#d_price", "60"); pg.evaluate("addMediaItem('photo', new Blob(['x'],{type:'image/jpeg'}))"); pg.wait_for_timeout(200); pg.click("text=Publish listing")
    assert "#f-home" in pg.url
    shot("f11_home_with_unlisted")
    # catalogue shows "My unlisted items" group
    pg.click(".nav >> text=Add"); pg.click(".vg >> text=Others")
    pg.wait_for_selector("#cg .vg"); assert pg.locator("#cg .vg").count() == 14, pg.locator("#cg .vg").count()
    pg.click("#cg .vg >> text=My unlisted items"); pg.wait_for_timeout(500)
    assert pg.locator(".crow").count() == 4
    pg.fill("#cq", "zzz unknown"); pg.wait_for_timeout(200); shot("f12_no_match")
    pg.click("text=Add as unlisted item"); pg.wait_for_timeout(200)
    assert pg.locator("#un").input_value() == "zzz unknown"
    pg.click("text=Add and select"); pg.wait_for_timeout(300)
    assert "#f-add" in pg.url, pg.url
    # auction from catalogue crop + quintal unit
    pg.click(".vg >> text=Paddy"); pg.fill("#d_qty", "12"); pg.select_option("#d_unit", "quintal")
    pg.click(".seg >> text=Auction"); pg.fill("#d_start", "2200"); pg.fill("#d_inc", "50"); pg.click(".chip >> text=30m")
    shot("f13_add_paddy_auction")
    pg.evaluate("addMediaItem('photo', new Blob(['x'],{type:'image/jpeg'}))"); pg.wait_for_timeout(200); pg.click("text=Publish listing")
    for _ in range(5): adv(20000)
    pg.click(".nav >> text=Offers"); shot("f14_offers")
    pg.goto("file://" + APPDIR + "/farmer.html#profile"); pg.wait_for_timeout(300); shot("f15_profile")
    assert pg.locator("text=I'm using the app as").count() == 0
    pg.evaluate("setLang('ta')"); pg.goto("file://" + APPDIR + "/farmer.html#f-add"); pg.wait_for_timeout(300); shot("f16_ta_add")
    pg.click(".vg >> text=மற்றவை"); pg.click("#cg .vg >> text=காய்கறிகள்"); pg.wait_for_timeout(600); shot("f17_ta_catalogue")
    pg.reload(); pg.wait_for_timeout(400)
    assert pg.evaluate("st.custom.filter(c=>!c.hidden).length") == 5
    for r in ["f-home", "f-add", "f-crops", "f-offers", "f-orders", "profile"]:
        pg.goto("file://" + APPDIR + "/farmer.html#" + r); pg.wait_for_timeout(250)
        w = pg.evaluate("document.documentElement.scrollWidth")
        if w > 412: errors.append(f"overflow {r}: {w}")
    b.close()

print("ERRORS:", errors if errors else "none")
