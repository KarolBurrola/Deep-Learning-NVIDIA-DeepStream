"""SpeedEstimator minimal: uncalibrated/demo only. No fake km/h."""
from collections import defaultdict


class SpeedEstimator:
    def __init__(self, mode="uncalibrated", fps=60.0, demo_scale=0.12):
        self.mode = mode
        self.fps = fps
        self.demo_scale = demo_scale  # px/s -> kmh sim, explicit demo only
        self.hist = defaultdict(list)  # track -> [(t, cx, by)]

    def update(self, track, cx, by, t):
        h = self.hist[track]
        h.append((t, cx, by))
        if len(h) > 600:
            self.hist[track] = h[-600:]
        return self.estimate(track)

    def estimate(self, track):
        h = self.hist.get(track, [])
        n = len(h)
        if n < 2:
            return {"state": "insufficient_evidence", "frames": n}
        t0, x0, y0 = h[0]
        t1, x1, y1 = h[-1]
        dt = t1 - t0
        if dt <= 0:
            dt = (n - 1) / self.fps if self.fps else 0.5
        import math
        dx, dy = x1 - x0, y1 - y0
        dist_px = math.hypot(dx, dy)
        vpx = dist_px / dt if dt > 0 else 0.0
        quality = min(1.0, n / 10.0) * (1.0 if dt >= 0.5 else dt / 0.5)
        out = {
            "state": "ok",
            "frames": n,
            "duration_s": dt,
            "dist_px": dist_px,
            "vpx_s": vpx,
            "quality": round(quality, 3),
        }
        if self.mode == "demo":
            out["speed_kmh"] = round(vpx * self.demo_scale, 1)
            out["simulated"] = True
        elif self.mode == "calibrated":
            out["state"] = "insufficient_evidence"  # no H verified in MVP
            out["reason"] = "no_verified_homography"
        return out
