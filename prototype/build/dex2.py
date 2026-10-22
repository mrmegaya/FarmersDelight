"""Multi-class DEX (v035) assembler for the FarmersDelight WebView shell.

Classes:
  MainActivity extends Activity        - WebView host, back button, file-chooser result,
                                          camera runtime permission, open app settings
  Chrome extends WebChromeClient       - <input type=file> -> system picker; getUserMedia -> camera permission
  Client extends WebViewClient         - tel: and other external links; fd://settings
"""
import os, struct, zlib, hashlib

PKG = os.environ.get("PKG", "com.farmersdelight.app")
P = "L" + PKG.replace(".", "/") + "/"
A, C, W = P + "MainActivity;", P + "Chrome;", P + "Client;"
ACT, WCC, WVC = "Landroid/app/Activity;", "Landroid/webkit/WebChromeClient;", "Landroid/webkit/WebViewClient;"
WV, WS, WIN = "Landroid/webkit/WebView;", "Landroid/webkit/WebSettings;", "Landroid/view/Window;"
VCB, FCP, PRQ = "Landroid/webkit/ValueCallback;", "Landroid/webkit/WebChromeClient$FileChooserParams;", "Landroid/webkit/PermissionRequest;"
WRR, URI, INT = "Landroid/webkit/WebResourceRequest;", "Landroid/net/Uri;", "Landroid/content/Intent;"
STR, OBJ, CTX, BUN, VIEW = "Ljava/lang/String;", "Ljava/lang/Object;", "Landroid/content/Context;", "Landroid/os/Bundle;", "Landroid/view/View;"
URL = "file:///android_asset/index.html"


def uleb(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: out.append(b | 0x80)
        else:
            out.append(b); return bytes(out)


def shorty(ret, params):
    s = lambda t: "L" if t[0] in "L[" else t
    return s(ret) + "".join(s(p) for p in params)


# ---------------------------------------------------------------- tiny assembler
class Asm:
    """Instructions are tuples; refs are resolved through `R` (a resolver)."""
    def __init__(self):
        self.ops = []

    def __getattr__(self, name):
        def add(*a):
            self.ops.append((name,) + a)
            return self
        return add


SIZES = {"inv": 3, "const4": 1, "const16": 2, "const": 3, "cstr": 2, "newi": 2, "newarr": 2, "aputo": 2, "aget": 2, "alen": 1,
         "igeto": 2, "iputo": 2, "ifeqz": 2, "ifnez": 2, "ifge": 2, "addlit8": 2, "goto": 1, "mres": 1, "mreso": 1, "ret": 1, "retv": 1, "label": 0}
INV = {"virtual": 0x6E, "super": 0x6F, "direct": 0x70, "static": 0x71, "interface": 0x72}


def assemble(asm, R):
    pos, labels = 0, {}
    for op in asm.ops:
        if op[0] == "label": labels[op[1]] = pos
        pos += SIZES[op[0]]
    out, pos = [], 0
    for op in asm.ops:
        k = op[0]
        if k == "inv":
            kind, m, regs = op[1], op[2], op[3:]
            r = list(regs) + [0] * (5 - len(regs)); c, d, e, f, g = r
            out += [(len(regs) << 12) | (g << 8) | INV[kind], R.m(m), (f << 12) | (e << 8) | (d << 4) | c]
        elif k == "const4": out += [((op[2] & 0xF) << 12) | (op[1] << 8) | 0x12]
        elif k == "const16": out += [(op[1] << 8) | 0x13, op[2] & 0xFFFF]
        elif k == "const": out += [(op[1] << 8) | 0x14, op[2] & 0xFFFF, (op[2] >> 16) & 0xFFFF]
        elif k == "cstr": out += [(op[1] << 8) | 0x1A, R.s(op[2])]
        elif k == "newi": out += [(op[1] << 8) | 0x22, R.t(op[2])]
        elif k == "newarr": out += [(op[2] << 12) | (op[1] << 8) | 0x23, R.t(op[3])]      # new-array vA, vB(size), type
        elif k == "aputo": out += [(op[1] << 8) | 0x4D, (op[3] << 8) | op[2]]             # aput-object vAA, vBB(array), vCC(index)
        elif k == "aget": out += [(op[1] << 8) | 0x44, (op[3] << 8) | op[2]]              # aget vAA, vBB(array), vCC(index)
        elif k == "alen": out += [(op[2] << 12) | (op[1] << 8) | 0x21]                     # array-length vA, vB
        elif k == "igeto": out += [(op[2] << 12) | (op[1] << 8) | 0x54, R.f(op[3])]
        elif k == "iputo": out += [(op[2] << 12) | (op[1] << 8) | 0x5B, R.f(op[3])]
        elif k in ("ifeqz", "ifnez"):
            off = labels[op[2]] - pos if R.real else 0
            out += [(op[1] << 8) | (0x38 if k == "ifeqz" else 0x39), off & 0xFFFF]
        elif k == "ifge":
            off = labels[op[3]] - pos if R.real else 0
            out += [(op[2] << 12) | (op[1] << 8) | 0x35, off & 0xFFFF]
        elif k == "addlit8": out += [(op[1] << 8) | 0xD8, ((op[3] & 0xFF) << 8) | op[2]]          # add-int/lit8 vAA, vBB, #CC
        elif k == "goto":
            off = labels[op[1]] - pos if R.real else 0
            assert -128 <= off < 128
            out += [((off & 0xFF) << 8) | 0x28]
        elif k == "mres": out += [(op[1] << 8) | 0x0A]
        elif k == "mreso": out += [(op[1] << 8) | 0x0C]
        elif k == "ret": out += [(op[1] << 8) | 0x0F]
        elif k == "retv": out += [0x000E]
        pos += SIZES[k]
    return out


# ---------------------------------------------------------------- program
M = dict(
    act_init=(ACT, "<init>", "V", ()), act_onCreate=(ACT, "onCreate", "V", (BUN,)), act_reqwf=(ACT, "requestWindowFeature", "Z", ("I",)),
    act_getWindow=(ACT, "getWindow", WIN, ()), act_setCV=(ACT, "setContentView", "V", (VIEW,)), act_onBack=(ACT, "onBackPressed", "V", ()),
    act_onAR=(ACT, "onActivityResult", "V", ("I", "I", INT)), act_reqPerm=(ACT, "requestPermissions", "V", ("[" + STR, "I")),
    act_startAR=(ACT, "startActivityForResult", "V", (INT, "I")), act_start=(ACT, "startActivity", "V", (INT,)),
    ctx_check=(CTX, "checkSelfPermission", "I", (STR,)), ctx_pkg=(CTX, "getPackageName", STR, ()),
    win_sbc=(WIN, "setStatusBarColor", "V", ("I",)),
    wv_init=(WV, "<init>", "V", (CTX,)), wv_gs=(WV, "getSettings", WS, ()), wv_load=(WV, "loadUrl", "V", (STR,)),
    wv_cgb=(WV, "canGoBack", "Z", ()), wv_gb=(WV, "goBack", "V", ()),
    wv_setWCC=(WV, "setWebChromeClient", "V", (WCC,)), wv_setWVC=(WV, "setWebViewClient", "V", (WVC,)),
    ws_js=(WS, "setJavaScriptEnabled", "V", ("Z",)), ws_dom=(WS, "setDomStorageEnabled", "V", ("Z",)), ws_tz=(WS, "setTextZoom", "V", ("I",)),
    ws_gesture=(WS, "setMediaPlaybackRequiresUserGesture", "V", ("Z",)),
    wcc_init=(WCC, "<init>", "V", ()), wvc_init=(WVC, "<init>", "V", ()),
    fcp_parse=(FCP, "parseResult", "[" + URI, ("I", INT)),
    int_clip=(INT, "getClipData", "Landroid/content/ClipData;", ()), clip_count=("Landroid/content/ClipData;", "getItemCount", "I", ()),
    clip_item=("Landroid/content/ClipData;", "getItemAt", "Landroid/content/ClipData$Item;", ("I",)), item_uri=("Landroid/content/ClipData$Item;", "getUri", URI, ()), fcp_intent=(FCP, "createIntent", INT, ()),
    vcb_recv=(VCB, "onReceiveValue", "V", (OBJ,)),
    prq_res=(PRQ, "getResources", "[" + STR, ()), prq_grant=(PRQ, "grant", "V", ("[" + STR,)), prq_deny=(PRQ, "deny", "V", ()),
    wrr_url=(WRR, "getUrl", URI, ()), uri_scheme=(URI, "getScheme", STR, ()), uri_parts=(URI, "fromParts", URI, (STR, STR, STR)),
    str_eq=(STR, "equals", "Z", (OBJ,)), intent_init=(INT, "<init>", "V", (STR, URI)),
    # own methods
    a_init=(A, "<init>", "V", ()), a_onCreate=(A, "onCreate", "V", (BUN,)), a_onBack=(A, "onBackPressed", "V", ()),
    a_onAR=(A, "onActivityResult", "V", ("I", "I", INT)), a_onRPR=(A, "onRequestPermissionsResult", "V", ("I", "[" + STR, "[I")),
    a_onPerm=(A, "onPerm", "V", (PRQ,)), a_settings=(A, "openSettings", "V", ()),
    c_init=(C, "<init>", "V", (A,)), c_fc=(C, "onShowFileChooser", "Z", (WV, VCB, FCP)), c_perm=(C, "onPermissionRequest", "V", (PRQ,)),
    w_init=(W, "<init>", "V", (A,)), w_over=(W, "shouldOverrideUrlLoading", "Z", (WV, WRR)),
)
F = dict(wv=(A, "wv", WV), cb=(A, "cb", VCB), pend=(A, "pend", PRQ), c_act=(C, "act", A), w_act=(W, "act", A))
CAM = "android.permission.CAMERA"


def code():
    """Returns {method_key: (regs, ins, outs, Asm)}."""
    X = {}
    a = Asm().inv("direct", "act_init", 0).retv(); X["a_init"] = (1, 1, 1, a)
    # onCreate: v0..v3, p0=v4, p1=v5
    a = Asm().inv("super", "act_onCreate", 4, 5).const4(0, 1).inv("virtual", "act_reqwf", 4, 0) \
        .inv("virtual", "act_getWindow", 4).mreso(0).const(1, 0xFF2F7D3B).inv("virtual", "win_sbc", 0, 1) \
        .newi(0, WV).inv("direct", "wv_init", 0, 4).iputo(0, 4, "wv") \
        .inv("virtual", "wv_gs", 0).mreso(1).const4(2, 1).inv("virtual", "ws_js", 1, 2).inv("virtual", "ws_dom", 1, 2) \
        .const16(2, 100).inv("virtual", "ws_tz", 1, 2).const4(2, 0).inv("virtual", "ws_gesture", 1, 2) \
        .newi(1, C).inv("direct", "c_init", 1, 4).inv("virtual", "wv_setWCC", 0, 1) \
        .newi(1, W).inv("direct", "w_init", 1, 4).inv("virtual", "wv_setWVC", 0, 1) \
        .cstr(1, URL).inv("virtual", "wv_load", 0, 1).inv("virtual", "act_setCV", 4, 0).retv()
    X["a_onCreate"] = (6, 2, 2, a)
    # onBackPressed: v0 v1, p0=v2
    a = Asm().igeto(0, 2, "wv").inv("virtual", "wv_cgb", 0).mres(1).ifeqz(1, "sup").inv("virtual", "wv_gb", 0).retv() \
        .label("sup").inv("super", "act_onBack", 2).retv()
    X["a_onBack"] = (3, 1, 1, a)
    # onActivityResult(I,I,Intent): v0..v5, p0=v6 p1=v7 p2=v8 p3=v9
    # Multiple picks come back as ClipData (FileChooserParams.parseResult only reads getData()).
    a = Asm().inv("super", "act_onAR", 6, 7, 8, 9).igeto(0, 6, "cb").ifeqz(0, "end") \
        .ifeqz(9, "parse").inv("virtual", "int_clip", 9).mreso(1).ifeqz(1, "parse") \
        .inv("virtual", "clip_count", 1).mres(2).ifeqz(2, "parse") \
        .newarr(3, 2, "[" + URI).const4(4, 0) \
        .label("loop").ifge(4, 2, "done").inv("virtual", "clip_item", 1, 4).mreso(5).inv("virtual", "item_uri", 5).mreso(5) \
        .aputo(5, 3, 4).addlit8(4, 4, 1).goto("loop") \
        .label("done").inv("interface", "vcb_recv", 0, 3).goto("clear") \
        .label("parse").inv("static", "fcp_parse", 8, 9).mreso(1).inv("interface", "vcb_recv", 0, 1) \
        .label("clear").const4(1, 0).iputo(1, 6, "cb") \
        .label("end").retv()
    X["a_onAR"] = (10, 4, 4, a)
    # onPerm(PermissionRequest): v0 v1 v2, p0=v3 p1=v4
    a = Asm().cstr(0, CAM).inv("virtual", "ctx_check", 3, 0).mres(1).ifnez(1, "ask") \
        .inv("virtual", "prq_res", 4).mreso(0).inv("virtual", "prq_grant", 4, 0).retv() \
        .label("ask").iputo(4, 3, "pend").const4(1, 1).newarr(2, 1, "[" + STR).const4(1, 0).aputo(0, 2, 1) \
        .const4(1, 1).inv("virtual", "act_reqPerm", 3, 2, 1).retv()
    X["a_onPerm"] = (5, 2, 3, a)
    # onRequestPermissionsResult(I,[String,[I): v0 v1, p0=v2 p1=v3 p2=v4 p3=v5
    a = Asm().igeto(0, 2, "pend").ifeqz(0, "end").const4(1, 0).iputo(1, 2, "pend") \
        .alen(1, 5).ifeqz(1, "deny").const4(1, 0).aget(1, 5, 1).ifnez(1, "deny") \
        .inv("virtual", "prq_res", 0).mreso(1).inv("virtual", "prq_grant", 0, 1).retv() \
        .label("deny").inv("virtual", "prq_deny", 0).label("end").retv()
    X["a_onRPR"] = (6, 4, 2, a)
    # openSettings(): v0..v3, p0=v4
    a = Asm().cstr(0, "package").inv("virtual", "ctx_pkg", 4).mreso(1).const4(2, 0).inv("static", "uri_parts", 0, 1, 2).mreso(1) \
        .newi(0, INT).cstr(2, "android.settings.APPLICATION_DETAILS_SETTINGS").inv("direct", "intent_init", 0, 2, 1) \
        .inv("virtual", "act_start", 4, 0).retv()
    X["a_settings"] = (5, 1, 3, a)
    # Chrome
    a = Asm().inv("direct", "wcc_init", 0).iputo(1, 0, "c_act").retv(); X["c_init"] = (2, 2, 1, a)
    # onShowFileChooser(WebView, ValueCallback, FileChooserParams): v0 v1 v2, p0=v3 p1=v4 p2=v5 p3=v6
    a = Asm().igeto(0, 3, "c_act").igeto(1, 0, "cb").ifeqz(1, "set").const4(2, 0).inv("interface", "vcb_recv", 1, 2) \
        .label("set").iputo(5, 0, "cb").inv("virtual", "fcp_intent", 6).mreso(1).const4(2, 2) \
        .inv("virtual", "act_startAR", 0, 1, 2).const4(1, 1).ret(1)
    X["c_fc"] = (7, 4, 3, a)
    a = Asm().igeto(0, 1, "c_act").inv("virtual", "a_onPerm", 0, 2).retv(); X["c_perm"] = (3, 2, 2, a)
    # Client
    a = Asm().inv("direct", "wvc_init", 0).iputo(1, 0, "w_act").retv(); X["w_init"] = (2, 2, 1, a)
    # shouldOverrideUrlLoading(WebView, WebResourceRequest): v0 v1 v2, p0=v3 p1=v4 p2=v5
    a = Asm().inv("interface", "wrr_url", 5).mreso(0).inv("virtual", "uri_scheme", 0).mreso(1) \
        .cstr(2, "file").inv("virtual", "str_eq", 2, 1).mres(2).ifeqz(2, "ext").const4(2, 0).ret(2) \
        .label("ext").cstr(2, "fd").inv("virtual", "str_eq", 2, 1).mres(2).ifeqz(2, "view") \
        .igeto(1, 3, "w_act").inv("virtual", "a_settings", 1).const4(2, 1).ret(2) \
        .label("view").newi(1, INT).cstr(2, "android.intent.action.VIEW").inv("direct", "intent_init", 1, 2, 0) \
        .igeto(2, 3, "w_act").inv("virtual", "act_start", 2, 1).const4(2, 1).ret(2)
    X["w_over"] = (6, 3, 3, a)
    return X


CLASSES = [  # (type, super, fields[(key, flags)], direct[(key, flags)], virtual[(key, flags)])
    (A, ACT, [("wv", 1), ("cb", 1), ("pend", 1)], [("a_init", 0x10001)],
     [("a_onCreate", 1), ("a_onBack", 1), ("a_onAR", 1), ("a_onRPR", 1), ("a_onPerm", 1), ("a_settings", 1)]),
    (C, WCC, [("c_act", 1)], [("c_init", 0x10001)], [("c_fc", 1), ("c_perm", 1)]),
    (W, WVC, [("w_act", 1)], [("w_init", 0x10001)], [("w_over", 1)]),
]


class Collect:
    real = False
    def __init__(self): self.ms, self.fs, self.ts, self.ss = set(), set(), set(), set()
    def m(self, k): self.ms.add(M[k]); return 0
    def f(self, k): self.fs.add(F[k]); return 0
    def t(self, x): self.ts.add(x); return 0
    def s(self, x): self.ss.add(x); return 0


def build():
    X = code()
    col = Collect()
    for k, (_, _, _, asm) in X.items():
        assemble(asm, col)
    methods = set(col.ms) | {M[k] for k in X}
    fields = set(col.fs) | {F[k] for c in CLASSES for k, _ in c[2]}
    types = set(col.ts) | {c[0] for c in CLASSES} | {c[1] for c in CLASSES}
    protos = set()
    for c, n, r, p in methods:
        types |= {c, r, *p}; protos.add((r, p))
    for c, n, t in fields:
        types |= {c, t}
    strings = set(col.ss) | types | {n for _, n, _, _ in methods} | {n for _, n, _ in fields} | {shorty(r, p) for r, p in protos}
    S = sorted(strings, key=lambda s: s.encode("utf-16-be"))
    si = {s: i for i, s in enumerate(S)}
    T = sorted(types, key=lambda t: si[t]); ti = {t: i for i, t in enumerate(T)}
    PR = sorted(protos, key=lambda rp: (ti[rp[0]], [ti[x] for x in rp[1]])); pi = {p: i for i, p in enumerate(PR)}
    FL = sorted(fields, key=lambda f: (ti[f[0]], si[f[1]], ti[f[2]])); fi = {f: i for i, f in enumerate(FL)}
    ML = sorted(methods, key=lambda m: (ti[m[0]], si[m[1]], pi[(m[2], m[3])])); mi = {m: i for i, m in enumerate(ML)}

    class Real:
        real = True
        m = staticmethod(lambda k: mi[M[k]]); f = staticmethod(lambda k: fi[F[k]])
        t = staticmethod(lambda x: ti[x]); s = staticmethod(lambda x: si[x])

    nS, nT, nP, nF, nM, nC = len(S), len(T), len(PR), len(FL), len(ML), len(CLASSES)
    off = 0x70
    s_off = off; off += 4 * nS
    t_off = off; off += 4 * nT
    p_off = off; off += 12 * nP
    f_off = off; off += 8 * nF
    m_off = off; off += 8 * nM
    c_off = off; off += 32 * nC
    data_off = off
    data = bytearray()
    align = lambda: data.extend(b"\0" * ((-len(data)) % 4))
    tl_off, tl_start = {}, data_off
    for r, p in PR:
        if p and p not in tl_off:
            align(); tl_off[p] = data_off + len(data)
            data += struct.pack("<I", len(p)) + b"".join(struct.pack("<H", ti[x]) for x in p)
    align()
    code_start, code_off = data_off + len(data), {}
    for k in X:
        align()
        regs, ins, outs, asm = X[k]
        insns = assemble(asm, Real)
        code_off[k] = data_off + len(data)
        data += struct.pack("<HHHHII", regs, ins, outs, 0, 0, len(insns)) + b"".join(struct.pack("<H", u) for u in insns)
    align()
    sd_start, sd_off = data_off + len(data), []
    for s in S:
        sd_off.append(data_off + len(data))
        data += uleb(len(s.encode("utf-16-le")) // 2) + s.encode("utf-8") + b"\0"
    cd_start, cd_offs = data_off + len(data), []
    for typ, sup, flds, dms, vms in CLASSES:
        cd_offs.append(data_off + len(data))
        cd = uleb(0) + uleb(len(flds)) + uleb(len(dms)) + uleb(len(vms))
        prev = 0
        for k, fl in sorted(flds, key=lambda x: fi[F[x[0]]]):
            cd += uleb(fi[F[k]] - prev) + uleb(fl); prev = fi[F[k]]
        for group in (dms, vms):
            prev = 0
            for k, fl in sorted(group, key=lambda x: mi[M[x[0]]]):
                cd += uleb(mi[M[k]] - prev) + uleb(fl) + uleb(code_off[k]); prev = mi[M[k]]
        data += cd
    align()
    map_off = data_off + len(data)
    items = [(0, 1, 0), (1, nS, s_off), (2, nT, t_off), (3, nP, p_off), (4, nF, f_off), (5, nM, m_off), (6, nC, c_off)]
    if tl_off: items.append((0x1001, len(tl_off), tl_start))
    items += [(0x2001, len(X), code_start), (0x2002, nS, sd_start), (0x2000, nC, cd_start), (0x1000, 1, map_off)]
    data += struct.pack("<I", len(items)) + b"".join(struct.pack("<HHII", t, 0, n, o) for t, n, o in items)

    ids = bytearray()
    ids += b"".join(struct.pack("<I", o) for o in sd_off)
    ids += b"".join(struct.pack("<I", si[t]) for t in T)
    for r, p in PR: ids += struct.pack("<III", si[shorty(r, p)], ti[r], tl_off.get(p, 0) if p else 0)
    for c, n, t in FL: ids += struct.pack("<HHI", ti[c], ti[t], si[n])
    for c, n, r, p in ML: ids += struct.pack("<HHI", ti[c], pi[(r, p)], si[n])
    for (typ, sup, *_), cdo in zip(CLASSES, cd_offs):
        ids += struct.pack("<IIIIIIII", ti[typ], 0x0001, ti[sup], 0, 0xFFFFFFFF, 0, cdo, 0)
    assert 0x70 + len(ids) == data_off
    size = data_off + len(data)
    hdr = bytearray(b"dex\n035\0" + b"\0" * 24) + struct.pack("<IIIIII", size, 0x70, 0x12345678, 0, 0, map_off)
    for n, o in ((nS, s_off), (nT, t_off), (nP, p_off), (nF, f_off), (nM, m_off), (nC, c_off), (len(data), data_off)):
        hdr += struct.pack("<II", n, o)
    dex = bytearray(hdr + ids + data)
    dex[12:32] = hashlib.sha1(dex[32:]).digest()
    dex[8:12] = struct.pack("<I", zlib.adler32(bytes(dex[12:])) & 0xFFFFFFFF)
    return bytes(dex)


if __name__ == "__main__":
    open("classes2.dex", "wb").write(build()); print("ok")
