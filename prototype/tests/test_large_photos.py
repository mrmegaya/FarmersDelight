from playwright.sync_api import sync_playwright
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))        # prototype/
APPDIR = os.path.join(ROOT, "app")                                        # run build/mkhtml.py first
MEDIA = os.path.join(ROOT, "tests", "media")                              # run tests/gen_testmedia.py first
SHOTS = os.path.join(ROOT, "tests", "screenshots")
TM=MEDIA; FARM="file://" + APPDIR + "/farmer.html"; errs=[]
with sync_playwright() as pw:
    b=pw.chromium.launch(args=["--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream"])
    pg=b.new_context(viewport={"width":412,"height":915},device_scale_factor=2,is_mobile=True,has_touch=True).new_page()
    pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(FARM); pg.wait_for_timeout(600)
    pg.click("text=Continue"); pg.fill("#nm","Mega Pillai"); pg.fill("#ph","9876543210"); pg.click("text=Send OTP"); pg.fill("#otp","1234"); pg.click("text=Verify and continue")
    pg.fill("#fv","Thondamuthur"); pg.click("#pm",position={"x":260,"y":110}); pg.click("text=Save farm")
    pg.click(".nav >> text=Add"); pg.wait_for_selector(".slots")
    # multi-pick: 50 MP photo + portrait + HEIC (bad) at once
    with pg.expect_file_chooser() as fc:
        pg.locator(".slots .slot").first.click(); pg.click(".sheet >> text=Photos from gallery")
    fc.value.set_files([f"{TM}/big50mp.jpg", f"{TM}/big50mp_portrait.jpg", f"{TM}/fake.heic"])
    pg.wait_for_function("!document.getElementById('busy')", timeout=30000); pg.wait_for_timeout(300)
    ph=pg.evaluate("livePhotos(UI.draft.media)")
    print("photos added:", len(ph), "| toast:", pg.locator("#toast").inner_text())
    for m in ph:
        info=pg.evaluate("""async (id)=>{const r=await fetch(MURL[id]);const bl=await r.blob();const i=new Image();i.src=MURL[id];await i.decode();
          const a=new Uint8Array(await bl.arrayBuffer());let ex=false;for(let k=0;k<Math.min(a.length,4000);k++){if(a[k]==0x45&&a[k+1]==0x78&&a[k+2]==0x69&&a[k+3]==0x66){ex=true;break}}
          return [i.naturalWidth,i.naturalHeight,Math.round(bl.size/1024),ex]}""", m["id"])
        print("  photo", info[0],"x",info[1], info[2],"KB", "EXIF present" if info[3] else "no EXIF/GPS")
    # camera snap still works
    pg.click(".slots .slot:not(.fill) >> nth=0"); pg.click(".sheet >> text=Take a photo")
    pg.wait_for_function("document.getElementById('cv') && document.getElementById('cv').videoWidth>0", timeout=10000)
    pg.click(".shutter2"); pg.wait_for_timeout(1500)
    print("after camera photo:", pg.evaluate("livePhotos(UI.draft.media).length"), "/ 3 ; hash:", pg.evaluate("location.hash"))
    b.close()
print("ERRORS:", errs or "none")
