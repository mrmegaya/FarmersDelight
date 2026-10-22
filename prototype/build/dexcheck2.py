"""Independent DEX reader: validates header, checksums, sort order, and disassembles code."""
import struct, sys, zlib, hashlib

d = open(sys.argv[1], "rb").read()
u32 = lambda o: struct.unpack_from("<I", d, o)[0]
u16 = lambda o: struct.unpack_from("<H", d, o)[0]
assert d[:8] == b"dex\n035\0"
assert u32(8) == zlib.adler32(d[12:]) & 0xFFFFFFFF, "adler"
assert d[12:32] == hashlib.sha1(d[32:]).digest(), "sha1"
assert u32(32) == len(d)
(nS, oS, nT, oT, nP, oP, nF, oF, nM, oM, nC, oC, dsz, doff) = struct.unpack_from("<14I", d, 56)
assert doff + dsz == len(d)


def uleb(o):
    r = s = 0
    while True:
        b = d[o]; o += 1
        r |= (b & 0x7F) << s; s += 7
        if b < 0x80:
            return r, o


def string(i):
    o = u32(oS + 4 * i)
    n, o = uleb(o)
    return d[o:o + n].decode()


S = [string(i) for i in range(nS)]
assert S == sorted(S), "strings unsorted"
T = [S[u32(oT + 4 * i)] for i in range(nT)]
assert [u32(oT + 4 * i) for i in range(nT)] == sorted(u32(oT + 4 * i) for i in range(nT))


def tlist(o):
    if not o:
        return []
    return [u16(o + 4 + 2 * k) for k in range(u32(o))]


P = []
for i in range(nP):
    sh, r, po = struct.unpack_from("<III", d, oP + 12 * i)
    P.append((r, tlist(po), S[sh]))
assert P == sorted(P, key=lambda x: (x[0], x[1])), "protos unsorted"
for r, ps, sh in P:
    exp = "".join("L" if t[0] in "L[" else t for t in [T[r]] + [T[x] for x in ps])
    assert sh == exp, (sh, exp)
FL = [struct.unpack_from("<HHI", d, oF + 8 * i) for i in range(nF)]
ML = [struct.unpack_from("<HHI", d, oM + 8 * i) for i in range(nM)]
assert ML == sorted(ML, key=lambda m: (m[0], m[2], m[1])), "methods unsorted"
fmt_m = lambda i: f"{T[ML[i][0]]}->{S[ML[i][2]]}({''.join(T[x] for x in P[ML[i][1]][1])}){T[P[ML[i][1]][0]]}"
fmt_f = lambda i: f"{T[FL[i][0]]}->{S[FL[i][2]]}:{T[FL[i][1]]}"
for i in range(nM):
    print("method", i, fmt_m(i))



def dis(co):
    regs, ins, outs, tries, dbg, n = struct.unpack_from("<HHHHII", d, co)
    print(f"   regs={regs} ins={ins} outs={outs} units={n}")
    U = [u16(co + 16 + 2 * k) for k in range(n)]
    pc = 0
    while pc < n:
        w = U[pc]; op = w & 0xFF; a = w >> 8
        if op in (0x6E, 0x6F, 0x70, 0x71, 0x72):
            cnt = w >> 12; g = (w >> 8) & 0xF; regsw = U[pc + 2]
            rr = [regsw & 0xF, (regsw >> 4) & 0xF, (regsw >> 8) & 0xF, regsw >> 12, g][:cnt]
            assert all(r < regs for r in rr)
            print(f"   {pc:3} invoke-{ {0x6E:'virtual',0x6F:'super',0x70:'direct',0x71:'static',0x72:'interface'}[op]} {rr} {fmt_m(U[pc+1])}"); pc += 3
        elif op == 0x12: print(f"   {pc:3} const/4 v{a & 0xF}, {w >> 12}"); pc += 1
        elif op == 0x13: print(f"   {pc:3} const/16 v{a}, {U[pc+1]}"); pc += 2
        elif op == 0x14: print(f"   {pc:3} const v{a}, {hex(U[pc+1] | U[pc+2] << 16)}"); pc += 3
        elif op == 0x0A: print(f"   {pc:3} move-result v{a}"); pc += 1
        elif op == 0x0C: print(f"   {pc:3} move-result-object v{a}"); pc += 1
        elif op == 0x22: print(f"   {pc:3} new-instance v{a}, {T[U[pc+1]]}"); pc += 2
        elif op in (0x5B, 0x54): print(f"   {pc:3} {'iput' if op==0x5B else 'iget'}-object v{a & 0xF}, v{w >> 12}, {fmt_f(U[pc+1])}"); pc += 2
        elif op == 0x1A: print(f"   {pc:3} const-string v{a}, {S[U[pc+1]]!r}"); pc += 2
        elif op == 0x23: print(f"   {pc:3} new-array v{a & 0xF}, v{w >> 12}, {T[U[pc+1]]}"); pc += 2
        elif op == 0x4D: print(f"   {pc:3} aput-object v{a}, v{U[pc+1] & 0xFF}, v{U[pc+1] >> 8}"); pc += 2
        elif op == 0x44: print(f"   {pc:3} aget v{a}, v{U[pc+1] & 0xFF}, v{U[pc+1] >> 8}"); pc += 2
        elif op == 0x21: print(f"   {pc:3} array-length v{a & 0xF}, v{w >> 12}"); pc += 1
        elif op == 0x35:
            tt = pc + struct.unpack('<h', struct.pack('<H', U[pc+1]))[0]; assert 0 <= tt < n
            print(f"   {pc:3} if-ge v{a & 0xF}, v{w >> 12}, ->{tt}"); pc += 2
        elif op == 0xD8: print(f"   {pc:3} add-int/lit8 v{a}, v{U[pc+1] & 0xFF}, #{U[pc+1] >> 8}"); pc += 2
        elif op == 0x28:
            tt = pc + struct.unpack('<b', bytes([w >> 8]))[0]; assert 0 <= tt < n
            print(f"   {pc:3} goto ->{tt}"); pc += 1
        elif op == 0x0F: print(f"   {pc:3} return v{a}"); pc += 1
        elif op in (0x38, 0x39) and op == 0x39:
            t = pc + struct.unpack('<h', struct.pack('<H', U[pc+1]))[0]
            assert 0 <= t < n; print(f"   {pc:3} if-nez v{a}, ->{t}"); pc += 2
        elif op == 0x38:
            t = pc + struct.unpack('<h', struct.pack('<H', U[pc+1]))[0]
            assert 0 <= t < n; print(f"   {pc:3} if-eqz v{a}, ->{t}"); pc += 2
        elif op == 0x0E: print(f"   {pc:3} return-void"); pc += 1
        else: raise SystemExit(f"unknown op {op:#x}")


for ci_ in range(nC):
  ci, acc, sup, itf, src, ann, cdo, sv = struct.unpack_from("<8I", d, oC + 32 * ci_)
  print("class", T[ci], "extends", T[sup])
  o = cdo
  sf, o = uleb(o); inf, o = uleb(o); dm, o = uleb(o); vm, o = uleb(o)
  last = 0
  for _ in range(sf + inf):
    fd, o = uleb(o); fa, o = uleb(o); last += fd; print(" field", fmt_f(last), hex(fa))
  for kind, cnt in (("direct", dm), ("virtual", vm)):
    last = 0
    for _ in range(cnt):
        md, o = uleb(o); ma, o = uleb(o); co, o = uleb(o)
        last += md
        print(f" {kind} {fmt_m(last)} flags={ma:#x}")
        dis(co)
# map list
mo = u32(52)
items = [struct.unpack_from("<HHII", d, mo + 4 + 12 * k) for k in range(u32(mo))]
offs = [it[3] for it in items]
assert offs == sorted(offs), "map unsorted"
print("map", [(hex(t), n, o) for t, _, n, o in items])
print("DEX OK")
