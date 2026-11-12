# Troubleshooting — SMART RADAR AI (DeepStream 9.2 en WSL2, RTX 4070)

## Driver insuficiente para el contenedor
Síntoma: `ERROR: container built for NVIDIA Driver Release 595.45 or later, but version X detected`, `Cuda failure: status=35`, `no element "nvh264dec"`.
Causa: DeepStream 9.2 exige driver Windows >=595.45.
Fix: web NVIDIA Drivers → RTX 4070 Laptop → Windows 11 → Game Ready → instalar → reboot. Verificar `nvidia-smi` en Win y WSL (misma versión).

## WSL roto tras actualizar driver (ld.so)
Síntoma: `Inconsistency detected by ld.so: _dl_setup_hash: Assertion ... failed` en cualquier comando `wsl`.
Causa: librerías WSL/libcuda desincronizadas tras el update.
Fix: `wsl --shutdown`, esperar 5s, reabrir Ubuntu.

## Docker: permission denied
Síntoma: `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
Causa: usuario fuera del grupo `docker` (`/var/run/docker.sock` es `root:docker`).
Fix: `sudo usermod -aG docker $USER` + `newgrp docker` (o re-login). Verificar `docker info`.

## PowerShell rompe `&`, `|` y `:v` al llamar a `wsl.exe`
Síntoma: URLs NGC con `?redirect=true&path=...` se cortan, `grep -E "a|b"` falla, `ffmpeg -q:v` da `Expected number for q: but found: v`.
Causa: PowerShell interpreta esos caracteres antes de pasarlos a `wsl.exe`.
Fix: no pasar comandos complejos inline; escribir `.sh`/`.py` en disco y ejecutar `wsl -d Ubuntu-26.04 -- bash /ruta/script.sh`. Regla: sin `&`, sin `|` y sin `:v` en la línea del `wsl`.

## Ruta YAML del contenedor
Síntoma: `YAML::BadFile, bad file: /home/marti/.../lpr_app_yolo.yml` dentro del contenedor.
Causa: se pasó ruta del host; dentro solo existen `/workspace` (repo) y `/work` (proyecto).
Fix: `./deepstream-lpr-app /workspace/configs/app/lpr_app_yolo.yml`.

## Decoder correcto
El plugin es `nvv4l2decoder` (y encoder `nvv4l2h264enc`), no `nvh264dec`. Los warnings de plugins de audio (`libmpg123`, `libFLAC`...) son irrelevantes.

## Tracker accuracy sin modelo ReID
Síntoma: `[NvMultiObjectTracker] Load engine failed ... TAO model file does not exist`, `Failed to initialize tracker context`.
Causa: `config_tracker_NvDCF_accuracy.yml` pide `resnet50_market1501.etlt`, ausente en el contenedor.
Fix: usar `config_tracker_NvDCF_perf.yml` (documentado como pendiente traer ReID).

## `frame_meta->frame_num` siempre 0
Síntoma: todo el export sale con `frame: 0`, tiempos colapsados a 0.0.
Causa: en este pipeline el campo no avanza.
Fix: contador propio (`g_exp_frame++` por frame_meta), igual que el `frame_number` de la app de referencia.

## `parent` de LPD siempre 0
Síntoma: `obj_meta->parent->object_id` es 0 en todas las placas.
Causa: el objeto padre no propaga el tracking ID en este punto del pipeline.
Fix: asociar placa→vehículo por solape espacial (centro de placa dentro del bbox del vehículo del mismo frame), no por puntero.
