"""Freeze the header at given times and screenshot each with headless Chrome.

Usage: python tools/header/frames.py <header.svg> <out_dir> <t1> <t2> ...
Each frame is the SVG with every animation paused at -t seconds (embers and the zombies'
gait keep their own phases). Set CHROME to the browser binary if it isn't the default.
"""
import os
import pathlib
import subprocess
import sys

CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
for t in sys.argv[3:]:
    freeze = ("svg *{animation-play-state:paused!important}"
              f"svg *:not(.em):not(.gait){{animation-delay:-{t}s!important}}")
    svg = src.replace("</style>", freeze + "</style>", 1)
    frame_svg = out / f"t{t}.svg"
    frame_svg.write_text(svg, encoding="utf-8")
    png = out / f"t{t}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={png}", "--window-size=1000,320", "--default-background-color=00000000",
                    frame_svg.resolve().as_uri()], check=True, capture_output=True, timeout=60)
    print(png)
