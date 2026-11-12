"""ViolationEngine minimal: stable track + reliable speed + over limit, dedup."""


class ViolationEngine:
    def __init__(self, cfg):
        s = cfg.get("speed", {})
        v = cfg.get("violations", {})
        self.limit = float(s.get("limit_kmh", 60))
        self.min_frames = int(s.get("min_track_frames", 10))
        self.min_dur = float(s.get("min_track_duration_seconds", 0.5))
        self.max_per_track = int(v.get("max_events_per_track", 1))
        self.count = {}

    def check(self, track, est, plate=None, conf=0.0, min_conf=0.85):
        frames = est.get("frames", 0)
        dur = est.get("duration_s", 0)
        if est.get("state") != "ok":
            return {"state": "insufficient_evidence"}
        if frames < self.min_frames or dur < self.min_dur:
            return {"state": "insufficient_evidence"}
        if est.get("quality", 0) < 0.4:
            return {"state": "manual_review", "reason": "low_quality"}
        kmh = est.get("speed_kmh")
        if kmh is None:
            return {"state": "no_violation", "reason": "uncalibrated_no_kmh"}
        if kmh <= self.limit:
            return {"state": "no_violation", "speed_kmh": kmh}
        if self.count.get(track, 0) >= self.max_per_track:
            return {"state": "no_violation", "reason": "duplicate_suppressed"}
        self.count[track] = self.count.get(track, 0) + 1
        plate_out = plate if (plate and conf >= min_conf) else "plate_unknown"
        return {
            "state": "possible_violation",
            "speed_kmh": kmh,
            "limit_kmh": self.limit,
            "plate": plate_out,
            "simulated": est.get("simulated", False),
        }
