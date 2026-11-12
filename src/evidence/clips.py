"""Burn ticketed tracks with FOLLOWING box (per-frame drawbox) + concat."""
import json
import subprocess
import sys
from pathlib import Path

out_d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs")
video = out_d / "lpr_annotated.mp4"
fps = 60.0
events = json.loads((out_d / "tracks.json").read_text()).get("events", [])[:5]
clips = []
for ev in events:
    ed = out_d / "tickets" / ev["event_id"]
    traj = json.loads((ed / "trajectory.json").read_text())
    ts = ev["timestamp_s"]
    t0, t1 = traj[0]["t"], traj[-1]["t"]
    start, dur = max(0, t0), max(0.5, min(5, t1 - t0))
    n = int(dur * fps)
    # per-frame box from trajectory (60fps video)
    chain, prev = [], "0:v"
    ni = 0
    for i in range(n):
        vt = start + i / fps
        b = min(traj, key=lambda r: abs(r["t"] - vt))
        if abs(b["t"] - vt) > 0.5:
            continue
        x, y, w, h = (int(b["l"]), int(b["t_y"]), int(b["w"]), int(b["h"]))
        nxt = f"v{ni + 1}"
        chain.append(f"[{prev}]drawbox=x={x}:y={y}:w={w}:h={h}:color=red:t=6:"
                     f"enable='eq(n,{i})'[{nxt}]")
        prev, ni = nxt, ni + 1
    txt = f"SIMULACION {ev['event_id']} track {ev['track_id']} {ev['speed_kmh']}kmh"
    chain.append(f"[{prev}]drawtext=text='{txt}':x=20:y=20:fontsize=28:"
                 f"fontcolor=white:box=1:boxcolor=black@0.7[vout]")
    filt = ed / "filter.txt"
    filt.write_text(";\n".join(chain))
    clip = ed / "clip.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error",
                        "-ss", str(start), "-i", str(video),
                        "-t", str(dur), "-filter_complex_script", str(filt),
                        "-map", "[vout]", "-map", "0:a?", str(clip)])
    if clip.exists() and clip.stat().st_size > 0:
        clips.append(clip)
    print(ev["event_id"], "boxes=", ni, "ok=", clip.exists())
lst = out_d / "tickets" / "clips.txt"
lst.write_text("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", str(lst), "-c", "copy", str(out_d / "multas_demo.mp4")],
               check=False)
print(f"clips={len(clips)} -> {out_d / 'multas_demo.mp4'}")
