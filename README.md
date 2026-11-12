# Smart Radar AI — control de velocidad con NVIDIA DeepStream

> **`SIMULACIÓN — SIN VALIDEZ LEGAL`**: velocidades demo, matrículas no
> identificadas (`plate_unknown`) y sin calibración métrica. Nada de aquí es una sanción real.

Sistema local (sin nube) que procesa un video de tráfico con
**DeepStream 9.2 + modelos TAO**: detecta vehículos, les asigna ID con tracker
NvDCF, intenta leer matrículas (LPDNet + LPRNet) y genera tickets simulados con
evidencia para los eventos que superan el límite configurado.

## Demo

https://github.com/KarolBurrola/Deep-Learning-NVIDIA-DeepStream/raw/refs/heads/main/outputs/demo_preview.mp4

Multados con box seguidor (10s). Completo 60s: [multas_full.mp4](https://github.com/KarolBurrola/Deep-Learning-NVIDIA-DeepStream/raw/refs/heads/main/outputs/multas_full.mp4). Anotado DeepStream: [lpr_annotated.mp4](https://github.com/KarolBurrola/Deep-Learning-NVIDIA-DeepStream/raw/refs/heads/main/outputs/lpr_annotated.mp4). Video fuente: [Release v0.1-mvp](https://github.com/KarolBurrola/Deep-Learning-NVIDIA-DeepStream/releases/tag/v0.1-mvp).

## Fotos

**1. Detección normal** — boxes + IDs persistentes solo en calzada hacia cámara
(`outputs/lpr_annotated.mp4`):

![Detección](docs/img/deteccion.jpg)

**2. Placas** — LPDNet recorta y LPRNet escribe el texto (`lpdn ...`); el modelo USA
falla en placas UK, así que todo va a `plate_unknown` + revisión manual:

![Placas](docs/img/placas_a.jpg)

**3. Multa simulada** — box rojo seguidor + texto sobre el multado (`outputs/multas_full.mp4`):

![Multa](docs/img/multa.jpg)

## Por qué DeepStream y no solo YOLO

- **Todo en GPU, sin copias**: decode → inferencia → tracking → OSD → encode
  vía `NvBufSurface`. Medido ~60fps con 3 modelos en una laptop de 8GB; un
  YOLO en Python+OpenCV rebota cada frame CPU↔GPU y rinde menos a igual hardware.
- **Cascada nativa** coche → placa → caracteres (PGIE→SGIE) con parser propio y
  FP16 por modelo vía TensorRT, en vez de pegar tres repos.
- **Tracking con IDs integrado** (NvDCF); en YOLO lo añades tú (ByteTrack).
- **Cuándo YOLO gana**: instalación `pip` vs contenedor 27GB, reentrenar a placas
  UK trivial vs TAO pesado, más comunidad. Para un prototipo rápido, YOLO habría
  llegado antes al primer resultado; aquí se eligió rendimiento a escala.

## Cómo se calcula la multa

Detalle completo en [`docs/multa-metodo.md`](docs/multa-metodo.md): foot-point del
bbox con timestamps del video → velocidad demo (`px/s × 0.12`, `simulated: true`)
→ motor de eventos (track estable, sin duplicados, `plate_unknown`) → ticket con
evidencia. Sin homografía verificada no hay km/h real; la rama `calibrated`
existe pero está inactiva. **100% modelos preentrenados NVIDIA, 0 epochs locales.**

## Uso

```bash
./scripts/run.sh --input ~/yolo-nvidia/carros.mp4 --config configs/demo.yaml --output outputs/
```

- `configs/default.yaml`: límite 60 (realista, 0 eventos en este video).
- `configs/demo.yaml`: límite 8 (genera tickets simulados para ver el formato).
- Salidas: `lpr_annotated.mp4`, `tracks.jsonl`, `detections.csv`, `tracks.json`,
  `summary.json`, `tickets/event_XXXX/{ticket.json,ticket.html,evidence.jpg,trajectory.json}`,
  `multas_demo.mp4`, `multas_full.mp4`.

Requisitos: WSL2 + driver Windows ≥595.45, Docker con GPU, `uv` + Python 3.13.
El video y los pesos no van al repo: pon tu MP4 donde quieras y pásalo con
`--input`; los pesos se bajan con `scripts/download-tao.sh`.
Ver [`docs/troubleshooting.md`](docs/troubleshooting.md) y [`plan.md`](plan.md).

## Estructura

`src/{speed,violations,evidence,mvp.py}` · `tests/unit/` · `scripts/` ·
`configs/` · `docs/` · `patches/` (cambios C++ sobre `deepstream_tao_apps`: exporter
JSONL, ROI en probe, `lpr_app_yolo.yml`) · `docker-compose.yml` (referencia).
Pesos TAO y videos no van al repo: `scripts/download-tao.sh`.
