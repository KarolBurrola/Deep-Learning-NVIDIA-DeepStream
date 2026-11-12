"""MVP runner: tracks.jsonl -> speed -> violations -> tickets + csv/json/summary."""
import csv
import json
import subprocess
import sys
from pathlib import Path


def load_cfg(p):
    import re
    txt = Path(p).read_text()
    # minimal yaml subset: key: value (no nesting beyond 1 level needed -> parse manually)
    cfg = {"speed": {}, "violations": {}, "plates": {}, "output": {}, "roi": {}}
    section = None
    for line in txt.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\w.*:$", line.strip()):
            section = line.strip()[:-1]
            continue
        m = re.match(r"^\s+(\w+):\s*(.+?)\s*$", line)
        if m and section in cfg:
            k, v = m.group(1), m.group(2).split("#")[0].strip()
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    if v in ("true", "false"):
                        v = v == "true"
            cfg[section][k] = v
    return cfg


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from speed.estimator import SpeedEstimator
    from violations.engine import ViolationEngine

    tracks_p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/tracks.jsonl")
    cfg_p = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("configs/default.yaml")
    out_d = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("outputs")
    video = Path(sys.argv[4]) if len(sys.argv) > 4 else out_d / "lpr_annotated.mp4"
    cfg = load_cfg(cfg_p)
    mode = cfg["speed"].get("mode", "uncalibrated")
    if mode == "calibrated":  # MVP has no verified H -> force uncalibrated/demo honesty
        mode = "uncalibrated"
    fps = 60.0
    est, eng = SpeedEstimator(mode=mode, fps=fps), ViolationEngine(cfg)
    min_conf = float(cfg["plates"].get("min_confidence", 0.85))
    try:
        poly = json.loads(cfg.get("roi", {}).get("polygon", "[]"))
    except ValueError:
        poly = []

    def in_roi(x, y):
        if not poly:  # no ROI configured -> accept all
            return True
        inside, n = False, len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
                inside = not inside
        return inside
    veh, lpd = {}, []
    for line in tracks_p.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        t = float(r["frame"]) / fps
        if r.get("kept", 1) == 0:
            continue
        if r["uid"] == 1:  # PGIE vehicle
            veh.setdefault(r["track"], []).append((t, r))
            cx, by = r["l"] + r["w"] / 2, r["t"] + r["h"]
            e = est.update(r["track"], cx, by, t)
            r["_est"] = e
        elif r["uid"] == 2 and r.get("plate"):  # LPD + LPR string
            # ponytail: parent ptr is 0 in this app; link by overlap instead
            lpd.append((r["frame"], r["plate"], r))
    (out_d / "tickets").mkdir(parents=True, exist_ok=True)
    rows, events, eid = [], [], 0
    def best_plate(tid, hist):
        fr1 = hist[0][1]["frame"]
        fr2 = hist[-1][1]["frame"]
        best = (None, None, None)
        for fr, p, r in lpd:
            if fr < fr1 or fr > fr2:
                continue
            px, py = r["l"] + r["w"] / 2, r["t"] + r["h"] / 2
            for t, v in hist:
                if v["frame"] != fr:
                    continue
                if v["l"] <= px <= v["l"] + v["w"] and v["t"] <= py <= v["t"] + v["h"]:
                    return p, t, r
            best = (p, t, r)
        return best

    for tid, hist in veh.items():
        last = hist[-1][1]
        e = last.get("_est", {})
        cx_last, by_last = last["l"] + last["w"] / 2, last["t"] + last["h"]
        roi_ok = in_roi(cx_last, by_last)
        p, pt, pr = best_plate(tid, hist)
        if not roi_ok:  # calzada opuesta: fuera de alcance
            res = {"state": "no_violation", "reason": "outside_roi"}
        else:
            res = eng.check(tid, e, p, 0.0 if p is None else 0.5, min_conf)
        # UK/US-mismatch: never trust raw strings -> plate_unknown for review
        if res.get("plate") not in (None, "plate_unknown"):
            res["plate"] = "plate_unknown"
            res["state"] = "manual_review" if res["state"] == "possible_violation" else res["state"]
        rows.append({"track": tid, "frames": e.get("frames"), "state": res["state"],
                     "speed_kmh": res.get("speed_kmh"), "plate": res.get("plate", "plate_unknown"),
                     "in_roi": roi_ok})
        if res["state"] in ("possible_violation", "manual_review") and res.get("speed_kmh") is not None:
            eid += 1
            ed = out_d / "tickets" / f"event_{eid:04d}"
            ed.mkdir(parents=True, exist_ok=True)
            ts = pt if pt is not None else hist[-1][0]
            ev = ed / "evidence.jpg"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(max(0, ts)),
                            "-i", str(video), "-frames:v", "1", "-q:v", "3", str(ev)], check=False)
            traj = [{"t": t, "l": r["l"], "t_y": r["t"], "w": r["w"], "h": r["h"]} for t, r in hist]
            (ed / "trajectory.json").write_text(json.dumps(traj))
            ticket = {"event_id": f"event_{eid:04d}", "track_id": tid, "plate": "plate_unknown",
                      "raw_lpr": p, "speed_kmh": res.get("speed_kmh"), "limit_kmh": eng.limit,
                      "timestamp_s": ts, "calibration": mode, "review": res["state"],
                      "simulated": True, "model": "TAO LPRNet-US (unreliable on UK)"}
            (ed / "ticket.json").write_text(json.dumps(ticket, indent=2))
            (ed / "ticket.html").write_text(
                f"<html><body><h1>SIMULACIÓN — SIN VALIDEZ LEGAL</h1>"
                f"<p>Evento {ticket['event_id']} track {tid} v={ticket['speed_kmh']}km/h "
                f"limite {eng.limit} t={ts:.2f}s estado={res['state']}</p></body></html>")
            events.append(ticket)
    with open(out_d / "detections.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["track", "frames", "state", "speed_kmh", "plate", "in_roi"])
        w.writeheader()
        w.writerows(rows)
    (out_d / "tracks.json").write_text(json.dumps({"mode": mode, "events": events}, indent=2))
    summary = {"frames": sum(1 for _ in open(tracks_p)) if tracks_p.exists() else 0,
               "tracks": len(veh), "plate_strings": len(lpd),
               "events": len(events), "mode": mode, "fps": fps,
               "note": "LPRNet-US unreliable on UK; all plates plate_unknown; demo speeds only"}
    (out_d / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
