"""Builds FarmersDelight.apk without the Android SDK:
binary AndroidManifest.xml, resources.arsc (launcher icon), classes.dex,
assets/index.html, aligned zip, APK Signature Scheme v2 (RSA-2048/SHA-256)."""
import struct, zlib, hashlib, os, sys, datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import dex2 as dexgen

PKG = os.environ.get("PKG", "com.farmersdelight.app")
LABEL = os.environ.get("LABEL", "FarmersDelight")
VERSION_CODE, VERSION_NAME = int(os.environ.get("VC", "1")), os.environ.get("VN", "1.0")
ANDROID_NS = "http://schemas.android.com/apk/res/android"
ICON_ID = 0x7F010000

# ---------------------------------------------------------------- string pool

def string_pool(strings):
    n = len(strings)
    offs, body = [], bytearray()
    for s in strings:
        offs.append(len(body))
        enc = s.encode("utf-16-le")
        assert len(s) < 0x8000
        body += struct.pack("<H", len(enc) // 2) + enc + b"\0\0"
    body += b"\0" * ((-len(body)) % 4)
    start = 28 + 4 * n
    size = start + len(body)
    return struct.pack("<HHIIIIII", 0x0001, 28, size, n, 0, 0, start, 0) + b"".join(
        struct.pack("<I", o) for o in offs) + body

# ---------------------------------------------------------------- manifest (AXML)
ATTR_IDS = {
    "theme": 0x01010000, "label": 0x01010001, "icon": 0x01010002, "name": 0x01010003,
    "exported": 0x01010010, "screenOrientation": 0x0101001E, "configChanges": 0x0101001F,
    "minSdkVersion": 0x0101020C, "versionCode": 0x0101021B, "versionName": 0x0101021C,
    "windowSoftInputMode": 0x0101022B, "required": 0x0101028E, "targetSdkVersion": 0x01010270, "allowBackup": 0x01010280,
}
STR_T, INT_DEC, INT_HEX, BOOL, REF = 0x03, 0x10, 0x11, 0x12, 0x01

TREE = ("manifest", [("", "package", STR_T, PKG), ("a", "versionCode", INT_DEC, VERSION_CODE),
                     ("a", "versionName", STR_T, VERSION_NAME)], [
    ("uses-sdk", [("a", "minSdkVersion", INT_DEC, 26), ("a", "targetSdkVersion", INT_DEC, 34)], []),
] + ([("uses-permission", [("a", "name", STR_T, "android.permission.CAMERA")], []),
      ("uses-feature", [("a", "name", STR_T, "android.hardware.camera"), ("a", "required", BOOL, False)], [])] if os.environ.get("CAMERA") else []) + [
    ("application", [("a", "label", STR_T, LABEL), ("a", "icon", REF, ICON_ID),
                     ("a", "allowBackup", BOOL, False)], [
        ("activity", [("a", "name", STR_T, PKG + ".MainActivity"), ("a", "exported", BOOL, True),
                      ("a", "screenOrientation", INT_DEC, 1), ("a", "configChanges", INT_HEX, 0x1FA0),
                      ("a", "windowSoftInputMode", INT_HEX, 0x10)], [
            ("intent-filter", [], [
                ("action", [("a", "name", STR_T, "android.intent.action.MAIN")], []),
                ("category", [("a", "name", STR_T, "android.intent.category.LAUNCHER")], []),
            ]),
        ]),
    ]),
])


def manifest():
    # attribute names with resource ids come first, in the same order as the id map
    used = []
    def walk(n):
        for ns, name, *_ in n[1]:
            if ns and name not in used:
                used.append(name)
        for c in n[2]:
            walk(c)
    walk(TREE)
    used.sort(key=lambda a: ATTR_IDS[a])
    strings = list(used)
    def S(s):
        if s not in strings:
            strings.append(s)
        return strings.index(s)
    S("android"); S(ANDROID_NS)
    nodes = bytearray()
    line = [1]
    def node(t, body):
        nodes.extend(struct.pack("<HHIII", t, 16, 16 + len(body), line[0], 0xFFFFFFFF) + body)
        line[0] += 1
    def emit(n):
        tag, attrs, kids = n
        recs = []
        for ns, name, typ, val in attrs:
            nsi = S(ANDROID_NS) if ns else 0xFFFFFFFF
            ni = S(name)
            if typ == STR_T:
                raw = S(val); data = raw
            else:
                raw = 0xFFFFFFFF
                data = (0xFFFFFFFF if val else 0) if typ == BOOL else val
            key = (0 if not ns else 1, ATTR_IDS.get(name, 0))
            recs.append((key, struct.pack("<IIIHBBI", nsi, ni, raw, 8, 0, typ, data)))
        recs.sort(key=lambda r: r[0])
        body = struct.pack("<IIHHHHHH", 0xFFFFFFFF, S(tag), 20, 20, len(recs), 0, 0, 0)
        node(0x0102, body + b"".join(r[1] for r in recs))
        for k in kids:
            emit(k)
        node(0x0103, struct.pack("<II", 0xFFFFFFFF, S(tag)))
    # pre-register strings in document order so indices are stable, then build
    def pre(n):
        S(n[0])
        for ns, name, typ, val in n[1]:
            S(name)
            if typ == STR_T:
                S(val)
        for k in n[2]:
            pre(k)
    pre(TREE)
    node(0x0100, struct.pack("<II", S("android"), S(ANDROID_NS)))
    emit(TREE)
    node(0x0101, struct.pack("<II", S("android"), S(ANDROID_NS)))
    pool = string_pool(strings)
    resmap = struct.pack("<HHI", 0x0180, 8, 8 + 4 * len(used)) + b"".join(
        struct.pack("<I", ATTR_IDS[a]) for a in used)
    body = pool + resmap + bytes(nodes)
    return struct.pack("<HHI", 0x0003, 8, 8 + len(body)) + body

# ---------------------------------------------------------------- resources.arsc
ICON_PATH = "res/drawable-xxxhdpi-v4/ic_launcher.png"


def arsc():
    gpool = string_pool([ICON_PATH])
    tpool = string_pool(["drawable"])
    kpool = string_pool(["ic_launcher"])
    spec = struct.pack("<HHIBBHI", 0x0202, 16, 20, 1, 0, 0, 1) + struct.pack("<I", 0x100)
    config = bytearray(64)
    struct.pack_into("<I", config, 0, 64)
    struct.pack_into("<H", config, 14, 640)   # density xxxhdpi
    struct.pack_into("<H", config, 24, 4)     # sdkVersion 4 (implied by density)
    entries = struct.pack("<HHI", 8, 0, 0) + struct.pack("<HBBI", 8, 0, 0x03, 0)
    hsz = 20 + 64
    tbody = struct.pack("<BBHII", 1, 0, 0, 1, hsz + 4) + bytes(config)
    typ = struct.pack("<HHI", 0x0201, hsz, hsz + 4 + len(entries)) + tbody + struct.pack("<I", 0) + entries
    name = PKG.encode("utf-16-le").ljust(256, b"\0")
    phdr = 288
    pkg_body = struct.pack("<I", 0x7F) + name + struct.pack(
        "<IIIII", phdr, 1, phdr + len(tpool), 1, 0)
    pkg_rest = tpool + kpool + spec + typ
    pkg = struct.pack("<HHI", 0x0200, phdr, phdr + len(pkg_rest)) + pkg_body + pkg_rest
    assert len(pkg_body) + 8 == phdr
    body = gpool + pkg
    return struct.pack("<HHII", 0x0002, 12, 12 + len(body), 1) + body

# ---------------------------------------------------------------- zip

def build_zip(entries):
    """entries: list of (name, bytes, store). Stored entries are 4-byte aligned."""
    out, cd = bytearray(), bytearray()
    dostime, dosdate = 0, (2026 - 1980) << 9 | 10 << 5 | 16
    for name, data, store in entries:
        nb = name.encode()
        crc = zlib.crc32(data) & 0xFFFFFFFF
        if store:
            comp, method = data, 0
        else:
            c = zlib.compressobj(9, zlib.DEFLATED, -15)
            comp, method = c.compress(data) + c.flush(), 8
        off = len(out)
        extra = b""
        if store:
            pad = (-(off + 30 + len(nb))) % 4
            extra = b"\0" * pad
        out += struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, method, dostime, dosdate, crc,
                           len(comp), len(data), len(nb), len(extra)) + nb + extra
        if store:
            assert len(out) % 4 == 0
        out += comp
        cd += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0, method, dostime, dosdate, crc,
                          len(comp), len(data), len(nb), 0, 0, 0, 0, 0, off) + nb
    cd_off = len(out)
    eocd = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(entries), len(entries), len(cd), cd_off, 0)
    return bytes(out), bytes(cd), eocd

# ---------------------------------------------------------------- v2 signing

def key_and_cert(path):
    if os.path.exists(path):
        pem = open(path, "rb").read()
        key = serialization.load_pem_private_key(pem, None)
        cert = x509.load_pem_x509_certificate(pem)
        return key, cert
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "FarmersDelight"),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FarmersDelight"),
                      x509.NameAttribute(NameOID.COUNTRY_NAME, "IN")])
    now = datetime.datetime(2026, 10, 1)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=365 * 30))
            .sign(key, hashes.SHA256()))
    open(path, "wb").write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                             serialization.NoEncryption())
                           + cert.public_bytes(serialization.Encoding.PEM))
    return key, cert


def lp(b):
    return struct.pack("<I", len(b)) + b


def chunk_digest(sections):
    digests = []
    for sec in sections:
        for i in range(0, len(sec), 1 << 20):
            c = sec[i:i + (1 << 20)]
            digests.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(c)) + c).digest())
    return hashlib.sha256(b"\x5a" + struct.pack("<I", len(digests)) + b"".join(digests)).digest()


def sign(content, cd, eocd, key, cert):
    ALG = 0x0103
    digest = chunk_digest([content, cd, eocd])
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    signed_data = lp(lp(struct.pack("<I", ALG) + lp(digest))) + lp(lp(cert_der)) + lp(b"")
    sig = key.sign(signed_data, padding.PKCS1v15(), hashes.SHA256())
    pub = key.public_key().public_bytes(serialization.Encoding.DER,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)
    signer = lp(signed_data) + lp(lp(struct.pack("<I", ALG) + lp(sig))) + lp(pub)
    v2 = lp(lp(signer))
    pair = struct.pack("<QI", 4 + len(v2), 0x7109871A) + v2
    size = len(pair) + 8 + 16
    block = struct.pack("<Q", size) + pair + struct.pack("<Q", size) + b"APK Sig Block 42"
    new_cd_off = len(content) + len(block)
    eocd2 = eocd[:16] + struct.pack("<I", new_cd_off) + eocd[20:]
    return content + block + cd + eocd2


def main(html_path, icon_path, out_path, key_path):
    entries = [
        ("AndroidManifest.xml", manifest(), False),
        ("classes.dex", dexgen.build(), False),
        ("resources.arsc", arsc(), True),
        (ICON_PATH, open(icon_path, "rb").read(), True),
        ("assets/index.html", open(html_path, "rb").read(), False),
    ]
    content, cd, eocd = build_zip(entries)
    key, cert = key_and_cert(key_path)
    apk = sign(content, cd, eocd, key, cert)
    open(out_path, "wb").write(apk)
    print(out_path, len(apk), "bytes")


if __name__ == "__main__":
    main(*sys.argv[1:5])
