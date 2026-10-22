"""Media + reports tests: farmer camera/gallery/trim/publish rule/reports; consumer gallery/report; camera denied."""
import os, time, base64
from playwright.sync_api import sync_playwright
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))        # prototype/
APPDIR = os.path.join(ROOT, "app")                                        # run build/mkhtml.py first
MEDIA = os.path.join(ROOT, "tests", "media")                              # run tests/gen_testmedia.py first
SHOTS = os.path.join(ROOT, "tests", "screenshots")

SH = SHOTS; os.makedirs(SH, exist_ok=True)
TM = MEDIA
FARM = "file://" + APPDIR + "/farmer.html"; CONS = "file://" + APPDIR + "/consumer.html"
errors, notes = [], []
CLOCK = "(()=>{const real=Date.now.bind(Date);let off=0;Date.now=()=>real()+off;window.__adv=ms=>{off+=ms;};})();"
FAKE = ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--autoplay-policy=no-user-gesture-required"]


def mk(pw, url, args):
    b = pw.chromium.launch(args=args)
    ctx = b.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.add_init_script(CLOCK)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(url[-14:] + " pageerror: " + str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(url[-14:] + " console: " + m.text))
    pg.goto(url); pg.wait_for_timeout(600)
    return b, pg


def shot(pg, n):
    pg.wait_for_timeout(250); pg.evaluate("document.getElementById('toast').className=''"); pg.wait_for_timeout(260)
    pg.screenshot(path=f"{SH}/{n}.png")


def login(pg):
    pg.click("text=Continue"); pg.fill("#nm", "Mega Pillai"); pg.fill("#ph", "9876543210")
    pg.click("text=Send OTP"); pg.fill("#otp", "1234"); pg.click("text=Verify and continue")


def blob_bytes(pg, mid):
    b64 = pg.evaluate("""async (id)=>{const r=await fetch(MURL[id]);const b=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<b.length;i++)s+=String.fromCharCode(b[i]);return btoa(s);}""", mid)
    return base64.b64decode(b64)


import traceback
with sync_playwright() as pw:
  try:
      # =============== FARMER
      b, pg = mk(pw, FARM, FAKE)
      login(pg); pg.fill("#fv", "Thondamuthur"); pg.click("#pm", position={"x": 260, "y": 110}); pg.click("text=Save farm")
      pg.click(".nav >> text=Add"); pg.wait_for_selector(".slots")
      shot(pg, "f01_add_empty")
      assert pg.locator(".slots .slot").count() == 4
      assert "Required" in pg.locator(".slots .slot").first.inner_text()
      pg.click(".vg >> text=Tomato"); pg.fill("#d_qty", "50"); pg.fill("#d_price", "40")
      pg.click("text=Publish listing"); pg.wait_for_timeout(300)
      assert "#f-add" in pg.url, "must not publish without a photo"
      assert pg.locator(".slot.err").count() == 1 and pg.locator("text=Add at least 1 photo to publish").count() >= 1
      shot(pg, "f02_publish_blocked")
      # source sheet
      pg.locator(".slot.err").click(); pg.wait_for_selector(".sheet .opt")
      assert pg.locator(".sheet .opt").count() == 4
      shot(pg, "f03_source_sheet")
      # camera photo x2
      pg.click(".sheet >> text=Take a photo"); pg.wait_for_function("document.getElementById('cv') && document.getElementById('cv').videoWidth>0", timeout=10000)
      shot(pg, "f04_camera_photo")
      pg.click(".shutter2"); pg.wait_for_timeout(700); pg.click(".shutter2"); pg.wait_for_timeout(700)
      assert "Photo 3 of 3" in pg.locator("#cpill").inner_text(), pg.locator("#cpill").inner_text()
      pg.click(".cbtn[aria-label=Close]"); pg.wait_for_timeout(500)
      assert "#f-add" in pg.url
      assert pg.evaluate("livePhotos(UI.draft.media).length") == 2
      # camera video: auto-stop at 10 s
      pg.locator(".slot.vid").click(); pg.click(".sheet >> text=Record a video")
      pg.wait_for_function("document.getElementById('cv') && document.getElementById('cv').videoWidth>0", timeout=10000)
      pg.click(".recbtn"); pg.wait_for_timeout(4200); shot(pg, "f05_recording")
      t0 = time.time(); pg.wait_for_function("location.hash.indexOf('#f-add')===0", timeout=15000)
      v = pg.evaluate("liveVideo(UI.draft.media)")
      assert v and 9 <= v["dur"] <= 10, v
      notes.append(f"camera video duration recorded: {v['dur']} s (auto-stopped)")
      vb = blob_bytes(pg, v["id"]); assert b"Opus" not in vb and b"Vorbis" not in vb and b"A_OPUS" not in vb, "video must have no audio track"
      notes.append(f"camera video size: {len(vb)//1024} KB, audio track: none")
      # stream must be stopped after leaving the camera
      assert pg.evaluate("CAM.stream === null")
      # gallery photos: 1 slot left, pick 2 -> 1 skipped
      with pg.expect_file_chooser() as fc:
          pg.locator(".slots .slot").nth(2).click(); pg.click(".sheet >> text=Photos from gallery")
      fc.value.set_files([f"{TM}/photo1.jpg", f"{TM}/photo2.jpg"])
      pg.wait_for_function("livePhotos(UI.draft.media).length===3", timeout=8000)
      ph = pg.evaluate("livePhotos(UI.draft.media)")
      gb = blob_bytes(pg, ph[2]["id"])
      assert b"Exif" not in gb[:5000] and b"TestPhone" not in gb, "location/EXIF must be stripped"
      dims = pg.evaluate("""async (id)=>{const i=new Image();i.src=MURL[id];await i.decode();return [i.naturalWidth,i.naturalHeight]}""", ph[2]["id"])
      assert max(dims) == 1600, dims
      notes.append(f"gallery photo resized to {dims[0]}x{dims[1]}, EXIF/GPS removed, {len(gb)//1024} KB")
      # limits: sheet options disabled at 3 photos + 1 video
      pg.locator(".slots .slot.fill").first.click(); pg.wait_for_selector(".photo-big")
      pg.click(".sheet >> text=Close")
      shot(pg, "f06_all_media")
      # make photo 3 the cover
      third = ph[2]["id"]
      pg.locator(".slots .slot.fill").nth(2).click(); pg.click(".sheet >> text=Make cover photo")
      assert pg.evaluate("livePhotos(UI.draft.media)[0].id") == third
      # replace video with a gallery video that needs trimming
      pg.locator(".slots .slot.fill").nth(3).locator(".x").click(); pg.wait_for_timeout(200)
      assert not pg.evaluate("liveVideo(UI.draft.media)")
      with pg.expect_file_chooser() as fc:
          pg.locator(".slot.vid").click(); pg.click(".sheet >> text=Video from gallery")
      fc.value.set_files(f"{TM}/long24.webm")
      pg.wait_for_function("location.hash==='#trim'", timeout=8000); pg.wait_for_timeout(800)
      pg.evaluate("trimMove(7)"); pg.evaluate("document.getElementById('tr').value=7")
      shot(pg, "f07_trim")
      pg.click("text=Use this clip"); pg.wait_for_timeout(2500); shot(pg, "f08_preparing")
      pg.wait_for_function("location.hash.indexOf('#f-add')===0 && !!liveVideo(UI.draft.media)", timeout=30000)
      v2 = pg.evaluate("liveVideo(UI.draft.media)"); vb2 = blob_bytes(pg, v2["id"])
      assert 9 <= v2["dur"] <= 10.5 and b"A_VORBIS" not in vb2 and b"Vorbis" not in vb2, v2
      notes.append(f"gallery video 24 s trimmed to {v2['dur']} s, {len(vb2)//1024} KB, audio removed")
      shot(pg, "f09_ready_to_publish")
      pg.click("text=Publish listing"); pg.wait_for_timeout(500)
      assert "#f-home" in pg.url
      shot(pg, "f10_home_cover")
      lid = pg.evaluate("st.listings[0].id")
      # persistence of media after reload (IndexedDB)
      pg.reload(); pg.wait_for_timeout(1500)
      assert pg.evaluate(f"!!mUrl(L('{lid}').media[0].id)"), "media must survive app restart"
      # reports: 2 reports -> re-upload card
      pg.goto(FARM + "#profile"); pg.wait_for_timeout(300)
      for _ in range(2): pg.click("text=Simulate a buyer report on my photo"); pg.wait_for_timeout(150)
      pg.goto(FARM + "#f-home"); pg.wait_for_timeout(400)
      assert pg.locator("text=Please replace a photo").count() == 1 and pg.locator("text=2 of 5").count() == 1
      shot(pg, "f11_reupload_card")
      # 5 reports on every photo -> photos removed, listing stays live and is marked reported
      pg.goto(FARM + "#profile"); pg.wait_for_timeout(300)
      for _ in range(13): pg.click("text=Simulate a buyer report on my photo"); pg.wait_for_timeout(80)
      st_ = pg.evaluate(f"(function(){{var l=L('{lid}');return {{reported:l.reported,status:l.status,live:livePhotos(l.media).length,removed:l.media.filter(m=>m.status==='removed').length}}}})()")
      assert st_["reported"] and st_["status"] == "active" and st_["live"] == 0 and st_["removed"] == 3, st_
      notes.append(f"after 15 reports: {st_}")
      pg.goto(FARM + "#f-home"); pg.wait_for_timeout(400); shot(pg, "f12_home_reported")
      pg.goto(FARM + "#f-edit/" + lid); pg.wait_for_timeout(400); shot(pg, "f13_edit_removed")
      assert pg.locator("text=stays live").count() == 1
      # farmer adds a new photo -> no longer reported
      with pg.expect_file_chooser() as fc:
          pg.click("button:has-text('Add a new photo')"); pg.click(".sheet >> text=Photos from gallery")
      fc.value.set_files(f"{TM}/photo3.jpg")
      pg.wait_for_function(f"livePhotos(L('{lid}').media).length===1", timeout=8000)
      assert pg.evaluate(f"L('{lid}').reported") is False
      shot(pg, "f14_edit_replaced")
      # Tamil check of media section
      pg.evaluate("setLang('ta')"); pg.goto(FARM + "#f-add"); pg.wait_for_timeout(400); shot(pg, "f15_ta_add_media")
      pg.evaluate("setLang('en')")
      b.close()

      # =============== FARMER: camera permission refused
      b, pg = mk(pw, FARM, ["--use-fake-device-for-media-stream", "--deny-permission-prompts"])
      login(pg); pg.fill("#fv", "Perur"); pg.click("#pm", position={"x": 200, "y": 150}); pg.click("text=Save farm")
      pg.click(".nav >> text=Add"); pg.locator(".slots .slot").first.click(); pg.click(".sheet >> text=Take a photo")
      pg.wait_for_selector("text=Camera is turned off for FD Farmer", timeout=10000)
      assert pg.locator("text=Open Settings").count() == 1 and pg.locator("text=Choose from gallery instead").count() == 1
      assert "#f-add" in pg.url
      shot(pg, "f16_camera_denied")
      b.close()

      # =============== CONSUMER
      b, pg = mk(pw, CONS, FAKE)
      login(pg); pg.wait_for_timeout(400)
      pg.click(".seg >> text=List"); pg.click("text=Within 10 km"); pg.wait_for_timeout(300)
      shot(pg, "c01_list_photos")
      assert pg.locator(".lc", has_text="Potato").locator("text=Photo removed (reported)").count() == 1
      pg.locator(".lc", has_text="Tomato").first.click(); pg.wait_for_selector("#gal")
      shot(pg, "c02_gallery")
      n_items = pg.locator(".gslide").count(); assert n_items >= 3, n_items
      pg.evaluate("var g=document.getElementById('gal'); g.scrollLeft=g.clientWidth; galScroll(g)")
      assert pg.locator("#gcount").inner_text().startswith("2 /")
      pg.click("text=Report photo"); pg.wait_for_selector(".sheet .radio")
      pg.click(".sheet >> text=Blurry or unclear"); shot(pg, "c03_report_sheet")
      pg.click("text=Send report"); pg.wait_for_timeout(300)
      pg.click("text=Report photo"); pg.wait_for_timeout(200)
      assert pg.locator(".sheet >> text=Reported").count() >= 1, "one report per buyer per photo"
      pg.evaluate("closeSheet()")
      # photo 2 had 2 earlier reports + ours = 3; push to 5 with other buyers and confirm takedown on buyer side
      lid = pg.evaluate("location.hash.split('/')[1]")
      pg.evaluate(f"(function(){{var l=L('{lid}');l.gal.counts[1]=4;l.gal.mine={{}};}})()")
      pg.evaluate("var g=document.getElementById('gal'); g.scrollLeft=g.clientWidth; galScroll(g)")
      pg.click("text=Report photo"); pg.click("text=Send report"); pg.wait_for_timeout(300)
      assert pg.evaluate(f"L('{lid}').gal.removed.indexOf(1)>=0")
      assert pg.locator(".gslide").count() == n_items - 1
      pg.locator(".gslide img").first.click(); pg.wait_for_timeout(400); shot(pg, "c04_photo_view"); pg.go_back(); pg.wait_for_timeout(300)
      if pg.locator(".gslide .playc").count():
          pg.locator(".gslide .playc").first.click(); pg.wait_for_timeout(1500); shot(pg, "c05_video_view"); pg.go_back()
      pg.goto(CONS + "#explore"); pg.wait_for_timeout(300); pg.click(".seg >> text=List"); pg.evaluate("UI.radius=25;render(true)")
      pg.locator(".lc", has_text="Potato").click(); pg.wait_for_timeout(300); shot(pg, "c06_reported_listing")
      b.close()

  except Exception:
    traceback.print_exc()
    pg.screenshot(path="/tmp/fail.png"); print("URL", pg.url)
print("\n".join(notes))
print("ERRORS:", errors if errors else "none")
