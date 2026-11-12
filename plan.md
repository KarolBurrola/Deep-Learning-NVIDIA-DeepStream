# plan.md — SMART RADAR AI (progreso real)

## Fase 0 — entorno [OK]
WSL2 2.7.3 + Ubuntu-26.04, driver Win 621.14 (>=595.45 tras update desde 551.78),
Docker 29.5.2 + CDI `--gpus all` OK, `uv 0.13.7` + Python 3.13.18, ffmpeg 8.0.1, vim.
VRAM 8GB con ~6GB usados en idle: cerrar apps GPU antes de inferir.

## Fase 1 — DeepStream [OK]
`ghcr.io/nvidia/deepstream:9.2-triton-multiarch` (27.4GB). `deepstream-app --version` → 9.2.
Decode `nvv4l2decoder` 300 buffers 4K en 0.62s; encode+save OK (`decode_test.mp4`).
Bloqueo resuelto: driver + `wsl --shutdown`. Solo `nvinfer`, sin Triton server.

## Video [OK]
`carros.mp4` 3840x2160 h264 60fps 60s 3600f 176MB, integridad OK.
Cámara fija elevada, autopista UK 2+2, tráfico denso lento. Placas UK legibles solo de cerca
(KN05 ZZK, AP05 JEO, EY09 VWS, DA07 CLX, CE61 MYL). Sin refs métricas → sin km/h real.

## Fase 2 — DS+LPR [OK con límite conocido]
`deepstream_tao_apps` compila en 9.2 sin cambios. Pesos TAO: TrafficCamNet 5.2M, LPD 915K, LPR-US 56M.
Pipeline 3600f a ~60.6fps → `lpr_annotated.mp4` 720p + `tracks.jsonl` (exporter JSONL propio en probe).
LPRNet-USA sobre UK: 564 strings, mayoría basura (`M*LVSU`), parciales (`EY09VMS` vs `EY09 VWS`).
Política: todo a `plate_unknown`/`manual_review`, nunca inventar.
44. Bugs del probe resueltos: `frame_num` siempre 0 (contador propio), `parent` siempre 0 (link por solape).
43. ROI polígono en probe: fuera no se cuenta/exporta/dibuja + gate 20px. `topk` 20→40 + umbral 0.4→0.2
para recall (los duplicados lejanos los mata el gate de tamaño).

## Fases 3-4 — velocidad + eventos [MVP]
`SpeedEstimator` (uncalibrated/demo, ventana, calidad) + `ViolationEngine` (estable+límite+dedup 1/track,
`plate_unknown`, estados no/insufficient/manual/possible). Tests OK.
Demo límite 8 → 2 eventos simulados. Límite 60 → 0 (correcto: atasco).

## Fase 5 — tickets [MVP]
`outputs/tickets/event_XXXX/{ticket.json,html,evidence.jpg,trajectory.json}` + `ticket.html` con
banner SIMULACIÓN. `multas_demo.mp4` (clips) y `multas_full.mp4` 60s con box seguidor + texto por evento.

## Fase 6 — CLI [MVP]
`scripts/run.sh --input --config --output` (DS + mvp + test). `configs/default.yaml` (60) y `demo.yaml` (8).
`README.md`, `docs/{architecture,calibration,troubleshooting}.md`. Falta: `docker-compose.yml`.

## Limitaciones conocidas
- Sin calibración métrica: no hay km/h real. Sin ReID: ID switches (~400 tracks/60s).
- LPR-USA no válido en UK. Recall PGIE con topk=40 verificado por overlay kept/dropped.
- Paralelización MCP-opencode intentada (2 docs) con `muse-spark-1.3-contributor`: jobs en cola sin
progreso → cancelados, docs escritos directamente.
