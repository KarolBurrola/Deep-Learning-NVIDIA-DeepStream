# Calibración — de píxeles a km/h

## Por qué píxeles no bastan
El desplazamiento en píxeles depende de distancia a cámara, focal y perspectiva: 10 px/s cerca son cm/s y lejos son m/s. Sin referencia métrica no hay km/h real. Este proyecto lo respeta con tres modos.

## Homografía
1. Definir ROI sobre la calzada (aquí polígono 1280x720 en `configs/*.yaml`, solo carriles hacia cámara).
2. Marcar 4+ correspondencias imagen↔plano de carretera con medidas reales (líneas de carril, bordes, marcas viales medidas con cinta).
3. Calcular homografía H (p. ej. `cv2.getPerspectiveTransform` / DLT).
4. Proyectar el foot-point (centro-inferior del bbox) a coordenadas métricas cada frame.
5. `speed_kmh = (distance_m / delta_time_s) * 3.6` con **timestamps del video**, nunca wall-clock.
6. Ventana temporal + suavizado robusto (mediana), incertidumbre y calidad por track.

## Modos
- `CALIBRATED`: solo con H verificada. Reporta km/h + incertidumbre.
- `UNCALIBRATED`: trayectorias y px/s. Sin km/h. (Estado inicial de este proyecto: sin refs métricas.)
- `DEMO`: factor de escala simulado, siempre con `simulated: true` y banner `SIMULACIÓN — SIN VALIDEZ LEGAL`.

## Referencias provisionales
La normativa UK de marcas viales (largos de línea/blanco estándar) puede servir como referencia aproximada para pruebas, nunca como prueba legal. Una multa real exige levantamiento topográfico, cadena de custodia y certificación del sistema: fuera del alcance de este MVP.

## Validación
Trayectorias sintéticas de distancia/tiempo conocidos; casos: FPS variable, frames perdidos, ID switches, bbox jitter, oclusiones, varias escalas. Con referencia independiente: MAE, RMSE y sesgo. Sin validación no se afirma precisión.
