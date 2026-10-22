"""Independent APK checks: zip integrity/alignment, AXML dump, arsc walk, v2 signature verification."""
import struct, sys, zipfile, hashlib, io
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

apk = open(sys.argv[1], "rb").read()
z = zipfile.ZipFile(io.BytesIO(apk))
assert z.testzip() is None
for i in z.infolist():
    data_off = i.header_offset + 30 + len(i.filename.encode()) + struct.unpack_from("<H", apk, i.header_offset + 28)[0]
    print(f"  {i.filename:45} {'stored' if i.compress_type == 0 else 'deflate':8} size={i.file_size:6} off%4={data_off % 4}")
    if i.filename == "resources.arsc":
        assert i.compress_type == 0 and data_off % 4 == 0


def pool(b, o):
    t, hs, sz, n, sc, fl, ss, _ = struct.unpack_from("<HHIIIIII", b, o)
    assert t == 1
    utf8 = fl & 0x100
    out = []
    for k in range(n):
        so = o + ss + struct.unpack_from("<I", b, o + hs + 4 * k)[0]
        if utf8:
            raise SystemExit("utf8 pool unexpected")
        ln = struct.unpack_from("<H", b, so)[0]
        out.append(b[so + 2:so + 2 + 2 * ln].decode("utf-16-le"))
    return out, sz


m = z.read("AndroidManifest.xml")
t, hs, size = struct.unpack_from("<HHI", m, 0)
assert t == 3 and size == len(m)
S, psz = pool(m, 8)
o = 8 + psz
t, hs, sz = struct.unpack_from("<HHI", m, o)
assert t == 0x180
ids = [struct.unpack_from("<I", m, o + 8 + 4 * k)[0] for k in range((sz - 8) // 4)]
o += sz
depth = 0
print("manifest:")
while o < len(m):
    t, hs, sz = struct.unpack_from("<HHI", m, o)
    if t == 0x102:
        ns, name, ast, asz, ac = struct.unpack_from("<IIHHH", m, o + 16)
        attrs = []
        for k in range(ac):
            ans, an, raw, vs, _, dt, data = struct.unpack_from("<IIIHBBI", m, o + 16 + ast + k * asz)
            rid = ids[an] if an < len(ids) else None
            val = S[data] if dt == 3 else hex(data) if dt in (1, 0x11) else (data != 0) if dt == 0x12 else data
            attrs.append(f"{'android:' if ans != 0xFFFFFFFF else ''}{S[an]}{'(' + hex(rid) + ')' if rid else ''}={val}")
        print("  " * (depth + 1) + "<" + S[name] + " " + " ".join(attrs) + ">")
        depth += 1
    elif t == 0x103:
        depth -= 1
    o += sz
assert depth == 0

r = z.read("resources.arsc")
t, hs, sz, pc = struct.unpack_from("<HHII", r, 0)
assert t == 2 and sz == len(r) and pc == 1
G, gsz = pool(r, 12)
po = 12 + gsz
t, hs, psize, pid = struct.unpack_from("<HHII", r, po)
assert t == 0x200 and hs == 288 and po + psize == len(r)
pname = r[po + 12:po + 12 + 256].decode("utf-16-le").rstrip("\0")
ts_off, _, ks_off = struct.unpack_from("<III", r, po + 268)
TS, _ = pool(r, po + ts_off)
KS, ksz = pool(r, po + ks_off)
c = po + ks_off + ksz
while c < po + psize:
    t, hs, csz = struct.unpack_from("<HHI", r, c)
    if t == 0x201:
        tid, _, _, ec, es = struct.unpack_from("<BBHII", r, c + 8)
        dens = struct.unpack_from("<H", r, c + 20 + 14)[0]
        eo = struct.unpack_from("<I", r, c + hs)[0]
        esz, efl, key = struct.unpack_from("<HHI", r, c + es + eo)
        vsz, _, vdt, vdata = struct.unpack_from("<HBBI", r, c + es + eo + esz)
        print(f"arsc: 0x{pid:02x}{tid:02x}0000 {TS[tid-1]}/{KS[key]} density={dens} -> {G[vdata]} (exists={G[vdata] in z.namelist()})")
        assert G[vdata] in z.namelist()
    c += csz
print("arsc package:", pname)

# ---- v2 signature
eocd = apk.rfind(b"PK\x05\x06")
cd_off = struct.unpack_from("<I", apk, eocd + 16)[0]
assert apk[cd_off - 16:cd_off] == b"APK Sig Block 42"
bsize = struct.unpack_from("<Q", apk, cd_off - 24)[0]
bstart = cd_off - bsize - 8
assert struct.unpack_from("<Q", apk, bstart)[0] == bsize
p = bstart + 8
v2 = None
while p < cd_off - 24:
    ln, pid2 = struct.unpack_from("<QI", apk, p)
    if pid2 == 0x7109871A:
        v2 = apk[p + 12:p + 8 + ln]
    p += 8 + ln
assert v2


def seq(b):
    out, i = [], 0
    while i < len(b):
        n = struct.unpack_from("<I", b, i)[0]; out.append(b[i + 4:i + 4 + n]); i += 4 + n
    return out


signer = seq(seq(v2)[0])[0]
sd, sigs, pub = seq(signer)
digests, certs, attrs = seq(sd)
alg, dg = struct.unpack_from("<I", seq(digests)[0])[0], seq(seq(digests)[0][4:])[0]
cert = x509.load_der_x509_certificate(seq(certs)[0])
salg, sig = struct.unpack_from("<I", seq(sigs)[0])[0], seq(seq(sigs)[0][4:])[0]
assert alg == salg == 0x0103
assert cert.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo) == pub
cert.public_key().verify(sig, sd, padding.PKCS1v15(), hashes.SHA256())
eocd_b = bytearray(apk[eocd:])
struct.pack_into("<I", eocd_b, 16, bstart)
secs = [apk[:bstart], apk[cd_off:eocd], bytes(eocd_b)]
ds = []
for s in secs:
    for i in range(0, len(s), 1 << 20):
        ch = s[i:i + (1 << 20)]; ds.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(ch)) + ch).digest())
top = hashlib.sha256(b"\x5a" + struct.pack("<I", len(ds)) + b"".join(ds)).digest()
assert top == dg, "content digest mismatch"
print("v2 signature OK, signer:", cert.subject.rfc4514_string(), "SHA-256 cert:", hashlib.sha256(seq(certs)[0]).hexdigest()[:32] + "…")
print("APK OK")
