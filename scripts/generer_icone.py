# Usage : python scripts/generer_icone.py ma3ia/assets/ma3ia.ico   (Windows)
#         python scripts/generer_icone.py build/ma3ia.icns           (macOS, fait par scripts/construire_app.sh)
"""Génère l'icône sans dépendance : carré graphite arrondi + faisceau de projecteur tungstène.
.ico : 16 à 256 px, PNG intégrés. .icns : 16 à 1024 px, PNG intégrés (types icp4…ic10)."""
import math, struct, sys, zlib

def png(n):
    S = 4  # suréchantillonnage pour l'anticrénelage
    rows = []
    for y in range(n):
        row = bytearray([0])
        for x in range(n):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(S):
                for sx in range(S):
                    u = (x + (sx + .5) / S) / n; v = (y + (sy + .5) / S) / n
                    # carré arrondi
                    r = .2; dx = max(abs(u - .5) - (.5 - r), 0); dy = max(abs(v - .5) - (.5 - r), 0)
                    if dx * dx + dy * dy > r * r: continue
                    c = [0x1b, 0x1c, 0x20]  # graphite uni
                    # projecteur en haut, faisceau trapézoïdal vers le bas
                    lamp = (u - .5) ** 2 / .018 + (v - .24) ** 2 / .006 <= 1
                    w = .07 + (v - .28) * .62
                    beam = .28 <= v <= .84 and abs(u - .5) <= w
                    if lamp: c = [0xe3, 0xc0, 0x7a]
                    elif beam:
                        a = .8 - (v - .28) * 1.1
                        c = [c[i] + ((0xe3, 0xc0, 0x7a)[i] - c[i]) * a for i in range(3)]
                    acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; acc[3] += 255
            k = S * S
            row += bytes([int(acc[0] / k), int(acc[1] / k), int(acc[2] / k), int(acc[3] / k)]) if acc[3] else bytes(4)
        rows.append(bytes(row))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")

sortie = sys.argv[1]
if sortie.lower().endswith(".icns"):
    # Types icns acceptant du PNG : icp4 16, icp5 32, icp6 64, ic07 128, ic08 256, ic09 512, ic10 1024 px.
    types = [(b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024)]
    corps = b"".join(t + struct.pack(">I", 8 + len(d)) + d for t, d in ((t, png(n)) for t, n in types))
    open(sortie, "wb").write(b"icns" + struct.pack(">I", 8 + len(corps)) + corps)
    sys.exit(0)

tailles = [16, 24, 32, 48, 64, 128, 256]
imgs = [png(n) for n in tailles]
off = 6 + 16 * len(imgs); ent = b""
for n, d in zip(tailles, imgs):
    ent += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(d), off); off += len(d)
open(sortie, "wb").write(struct.pack("<HHH", 0, 1, len(imgs)) + ent + b"".join(imgs))
