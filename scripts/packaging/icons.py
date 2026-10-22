"""Build native icon containers on macOS; preserve the generated PNG unchanged."""

import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    source = ROOT / "src/echo_heist/resources/assets/branding/concepts/core.png"
    output = ROOT / "packaging/icons"
    output.mkdir(exist_ok=True)
    work = ROOT / "output/cinematic-startup/icons.iconset"
    work.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size * scale),
                    str(size * scale),
                    str(source),
                    "--out",
                    str(work / name),
                ],
                check=True,
                capture_output=True,
            )
    subprocess.run(
        ["iconutil", "-c", "icns", str(work), "-o", str(output / "echo-heist.icns")], check=True
    )
    # PNG-compressed ICO entries are supported by the Windows V1 target.
    sizes = (16, 32, 128, 256)
    images = [(work / f"icon_{size}x{size}.png").read_bytes() for size in sizes]
    offset = 6 + len(sizes) * 16
    directory = bytearray(struct.pack("<HHH", 0, 1, len(sizes)))
    for size, image in zip(sizes, images, strict=True):
        directory.extend(
            struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(image), offset)
        )
        offset += len(image)
    (output / "echo-heist.ico").write_bytes(bytes(directory) + b"".join(images))
    print("Built macOS ICNS and Windows ICO from the selected original core concept")


if __name__ == "__main__":
    main()
