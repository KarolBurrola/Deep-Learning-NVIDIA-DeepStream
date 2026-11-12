# Cómo se calcula la multa — SMART RADAR AI

> `SIMULACIÓN — SIN VALIDEZ LEGAL`. Nada de lo aquí descrito constituye una sanción real:
> velocidades demo, placas no identificadas (`plate_unknown`) y sin calibración métrica.

## 1. Modelos: 100% preentrenados, 0 epochs locales

En este proyecto **no se entrenó ningún modelo**. No hay epochs, ni dataset de
entrenamiento, ni fine-tuning. Todo se descargó de NVIDIA NGC (TAO) y se usa tal cual:

| Etapa | Modelo | Peso | Origen |
|---|---|---|---|
| Detección vehículos (PGIE) | TrafficCamNet (ResNet18 podado) | `resnet18_trafficcamnet_pruned.onnx` 5.2M | NGC `nvidia/tao/trafficcamnet` |
| Detección placas (SGIE) | LPDNet-USA podado | `LPDNet_usa_pruned_tao5.onnx` 915K | NGC `nvidia/tao/lpdnet` |
| Lectura placas (SGIE) | LPRNet-USA baseline18 | `us_lprnet_baseline18_deployable.onnx` 56M | NGC `nvidia/tao/lprnet` |

Dato del fabricante (model card LPRNet): entrenado por NVIDIA con ~310.000 placas
USA + ~100.000 del dataset chino CCPD. Eso explica su rendimiento en UK: sobre
nuestro video produce mayormente basura (`MWSLVSU`, `MM51VSU`) con aciertos
parciales (`EY09VMS` frente a la real `EY09 VWS`). Por eso **toda lectura se
descarta** y el ticket sale como `plate_unknown` + `manual_review`.
Lo único "compilado" en local son los engines TensorRT FP16 (conversión de
formato, no entrenamiento) y el binario de la app de referencia.

Si algún día se reentrena con placas UK, aquí se registrarán: dataset, epochs,
hiperparámetros y métricas. Hoy esa sección está vacía por diseño.

## 2. Cálculo paso a paso (modo demo, el activo)

1. DeepStream vuelca `tracks.jsonl`: un JSON por objeto y frame
   (`frame, uid, cls, track, bbox, plate, kept`). Solo calzada hacia cámara
   (polígono ROI en probe) y vehículos ≥20px.
2. `SpeedEstimator` agrupa por `track`: toma el foot-point (centro-inferior del
   bbox) con timestamp del video (`t = frame / 60`) y mide desplazamiento en
   píxeles sobre ventana de hasta 600 observaciones.
3. Conversión demo: `speed_kmh = vpx_s * 0.12`, marcada `simulated: true`.
   El 0.12 es un factor arbitrario de visualización, no una calibración.
4. `ViolationEngine` genera evento solo si: track estable (≥10 frames, ≥0.5s,
   calidad ≥0.4), `speed_kmh` supera el límite, y no hay evento previo del track
   (`max_events_per_track: 1`). Placa: siempre `plate_unknown` (confianza LPR
   insuficiente en UK).
5. Por evento: carpeta `tickets/event_XXXX/` con `ticket.json`, `ticket.html`,
   `evidence.jpg` (frame del instante), `trajectory.json` y clip con box seguidor
   en `multas_demo.mp4` / `multas_full.mp4`.

Resultado medido en `carros.mp4` (60s, 3600 frames, ~60.6fps):
`139800` registros, `401` tracks, `1134` lecturas LPR descartadas,
`2` eventos con límite demo 8 (track 430: 8.5 km/h en t=30.33s;
track 509: 8.4 km/h en t=36.28s). Con límite 60: `0` eventos (correcto, es un atasco).
El camino `calibrated` (`kmh = m/s*3.6` con homografía) está implementado como
rama pero inactivo: sin referencias métricas verificadas no hay km/h real.

## 3. Herramientas usadas

DeepStream 9.2 (`nvinfer` PGIE+2×SGIE, tracker NvDCF `perf`, `nvv4l2decoder`,
`nvv4l2h264enc`, OSD), TensorRT (engines FP16 generados al primer run),
GStreamer, Docker 29.5 + NVIDIA Container Toolkit (CDI `--gpus all`), WSL2 +
driver Windows 621.14, `uv` + Python 3.13 (`SpeedEstimator`, `ViolationEngine`,
`tickets`, tests), ffmpeg 8 (evidencias, clips, concatenados), vim.
Contenedor: `ghcr.io/nvidia/deepstream:9.2-triton-multiarch` (27.4GB).
Sin Triton Server: `nvinfer` directo.

## 4. Por qué DeepStream y no YOLO

A favor de DeepStream+TAO en este proyecto: pipeline 100% GPU sin copias
(decode→infer→track→OSD→encode, `NvBufSurface`), 60fps reales con 3 modelos en
8GB; cascada PGIE→SGIE con parser custom y precisiones por modelo; tracker con
IDs integrado; modelos combinados detector+LPD+LPR.

A favor de YOLO (consta en acta): instalación `pip` frente a 27GB + driver
≥595.45; reentrenar a placas UK es trivial en Ultralytics frente a TAO;
comunidad e iteración más rápidas. Para un prototipo offline pequeño,
YOLOv8+ByteTrack+OCR habría dado primer resultado antes.

Decisión: DeepStream por rendimiento a escala y pipeline completo en GPU
(objetivo del encargo); YOLO queda como alternativa si se prioriza agilidad
de reentreno UK. Límites vistos aquí que YOLO también sufriría: IDs inestables
sin ReID (~400 tracks/60s) y necesidad de calibración métrica para km/h real.
