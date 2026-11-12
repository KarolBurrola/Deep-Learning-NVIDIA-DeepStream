# architecture

- Decoder GStreamer -> PGIE TrafficCamNet -> nvtracker NvDCF -> SGIE LPDNet -> SGIE LPRNet -> OSD -> annotated.mp4 + json
- `nvinfer` directo, sin Triton Server.
- LPRNet-USA no lee placas UK (KN05 ZZK etc): guardar crops + conf, `plate_unknown` para revision.
- Velocidad: homografia solo con refs verificadas (`calibrated`); si no, `uncalibrated` (px/trayectoria) o `demo` etiquetado. Formula `kmh = m/s*3.6` con timestamps del video.
- VRAM 8GB: batch 1, FP16, 1 stream offline, cerrar apps GPU.
