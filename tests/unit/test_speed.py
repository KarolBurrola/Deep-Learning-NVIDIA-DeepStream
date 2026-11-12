import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from speed.estimator import SpeedEstimator

e = SpeedEstimator(mode="uncalibrated", fps=60.0)
for i in range(12):
    r = e.update(1, 100 + i * 5, 500, i / 60.0)
assert r["frames"] == 12 and r["state"] == "ok" and "speed_kmh" not in r, r
e2 = SpeedEstimator(mode="demo", fps=60.0)
for i in range(12):
    r2 = e2.update(7, 100 + i * 5, 500, i / 60.0)
assert r2.get("simulated") is True and r2["speed_kmh"] > 0, r2
print("speed tests OK")
