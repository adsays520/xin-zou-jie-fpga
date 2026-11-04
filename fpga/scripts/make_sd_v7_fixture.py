from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests/runtime_temp"
OUT.mkdir(parents=True, exist_ok=True)


def make_image(case=0, real_piano=False):
    base, fat_size, data_start = 2048, 1024, 2048 + 32 + 2048
    sectors = {}

    def sector(address):
        return sectors.setdefault(address, bytearray(512))

    def put(target, offset, value, size=4):
        target[offset:offset + size] = value.to_bytes(size, "little")

    boot = sector(0)
    boot[510:] = b"\x55\xaa"
    boot[450] = 0x0c
    put(boot, 454, base)
    put(boot, 458, 131072)
    boot = sector(base)
    boot[510:] = b"\x55\xaa"
    put(boot, 11, 512, 2)
    boot[13], boot[16] = 1, 2
    put(boot, 14, 32, 2)
    put(boot, 32, 131072)
    put(boot, 36, fat_size)
    put(boot, 44, 2)
    put(sector(base + 32), 8, 0x0fffffff)
    directory = sector(data_start)

    def file_entry(name, entry, start, payload, size=None):
        directory[entry:entry + 11] = name
        directory[entry + 11] = 0x20
        put(directory, entry + 26, start, 2)
        put(directory, entry + 28, len(payload) if size is None else size)
        clusters = [start + 7 * index for index in range((len(payload) + 511) // 512)]
        for index, cluster in enumerate(clusters):
            following = clusters[index + 1] if index + 1 < len(clusters) else 0x0fffffff
            put(sector(base + 32 + cluster // 128), (cluster % 128) * 4, following)
            data = payload[index * 512:(index + 1) * 512]
            sector(data_start + cluster - 2)[:len(data)] = data
        return clusters

    piano = (ROOT / "sd_card/PIANOSMS.BIN").read_bytes() if real_piano else bytes(512)
    file_entry(b"PIANOSMSBIN", 0, 3, piano)
    drums = bytearray((ROOT / "sd_card/DRUMS.BIN").read_bytes())
    if case == 3:
        drums[777] ^= 1
    if case != 1:
        clusters = file_entry(b"DRUMS   BIN", 32, 7000, drums, 3071 if case == 2 else None)
        if case == 4:
            put(sector(base + 32 + clusters[0] // 128), (clusters[0] % 128) * 4, 0x0fffffff)
    entries = sorted(sectors.items())
    assert len(entries) < 800
    prefix = "sd0" if real_piano else f"drum_sd{case}"
    (OUT / f"{prefix}_lba.hex").write_text("".join(f"{address:08x}\n" for address in
        [entry[0] for entry in entries] + [0xffffffff] * (800 - len(entries))), encoding="utf-8")
    image = b"".join(entry[1] for entry in entries) + bytes((800 - len(entries)) * 512)
    (OUT / f"{prefix}_data.hex").write_text("".join(f"{value:02x}\n" for value in image), encoding="utf-8")


if __name__ == "__main__":
    for selected_case in range(7):
        make_image(selected_case)
    make_image(real_piano=True)
    print("Generated fragmented FAT32 fixtures for piano and DRUMS.BIN")
