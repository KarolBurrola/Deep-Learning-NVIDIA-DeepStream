"""Burn ALL ticketed tracks (following boxes) into full-length multas_full.mp4."""
import json
import subprocess
import sys
from pathlib import Path

out_d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs")
video = out_d / "lpr_annotated.mp4"
fps = 60.0
events = json.loads((out_d / "tracks.json").read_text()).get("events", [])
chain, prev, ni, nb = [], "0:v", 0, 0
for ev in events:
    ed = out_d / "tickets" / ev["event_id"]
    tj = ed / "trajectory.json"
    if not tj.exists():
        continue
    traj = json.loads(tj.read_text())
    fr0, fr1 = None, None
    for r in traj:
        fr = int(round(r["t"] * fps))
        fr0 = fr if fr0 is None else min(fr0, fr)
        fr1 = fr if fr1 is None else max(fr1, fr)
        x, y, w, h = (int(r["l"]), int(r["t_y"]), int(r["w"]), int(r["h"]))
        nxt = f"v{ni + 1}"
        chain.append(f"[{prev}]drawbox=x={x}:y={y}:w={w}:h={h}:color=red:t=4:"
                     f"enable='eq(n,{fr})'[{nxt}]")
        prev, ni, nb = nxt, ni + 1, nb + 1
    if fr0 is not None:
        txt = f"SIMULACION {ev['event_id']} track {ev['track_id']} {ev['speed_kmh']}kmh"
        nxt = f"v{ni + 1}"
        chain.append(f"[{prev}]drawtext=text='{txt}':x=20:y={20 + (len(chain) % 5) * 36}:"
                     f"fontsize=24:fontcolor=white:box=1:boxcolor=black@0.7:"
                     f"enable='between(n,{fr0},{fr1})'[{nxt}]")
        prev, ni = nxt, ni + 1
filt = out_d / "tickets" / "full_filter.txt"
filt.write_text(";\n".join(chain) + f"\n[{prev}]null[vout]\n".replace(f"[v{ni}]null", f"[{prev}]null") if False else ";\n".join(chain))
# fix last label to vout
txt = filt.read_text().rsplit(f"[v{ni}]", 1)
filt.write_text(txt[0] + "[vout]")
print("boxes=", nb, "events=", len(events))
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
                    "-filter_complex_script", str(filt),
                    "-map", "[vout]", "-map", "0:a?",
                    "-preset", "veryfast", str(out_d / "multas_full.mp4")])
print("done", out_d / "multas_full.mp4")
