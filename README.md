# Departure Guardian

Integración para Home Assistant que avisa cuando armas la alarma (`alarm_control_panel`)
con algo que debería estar apagado o cerrado: horno encendido, ventana abierta, enchufe
consumiendo por encima de un umbral.

No bloquea el armado — solo manda una notificación push detallada con lo que se quedó
encendido/abierto, para que decidas si vuelves.

## Instalación

### Vía HACS (repositorio personalizado)

1. HACS → Integraciones → menú (⋮) → Repositorios personalizados.
2. Añade la URL de este repositorio, categoría "Integration".
3. Instala "Departure Guardian" y reinicia Home Assistant.

### Manual

Copia `custom_components/departure_guardian` a `<config>/custom_components/` y reinicia.

## Configuración

Ajustes → Dispositivos y servicios → Añadir integración → Departure Guardian.

1. Selecciona tu entidad `alarm_control_panel` (Prosegur u otra).
2. Indica el servicio de notificación a usar (ej. `mobile_app_tu_movil`, sin el prefijo `notify.`).
3. Desde las opciones de la integración, añade las entidades a vigilar. Hay dos formas:
   - **Sugerir entidades automáticamente**: escanea las entidades ya expuestas por tus
     integraciones instaladas (por `device_class`, no por nombre de integración) y te
     propone sensores de puerta/ventana/apertura y sensores de consumo en W para que
     elijas cuáles vigilar con un clic.
   - **Añadir entidad a vigilar**: manual, para cualquier entidad que la sugerencia
     automática no detecte.

   Tipos de vigilancia:
   - **binary**: sensor on/off (horno, ventana, puerta). Se avisa si su estado coincide
     con el "estado problema" configurado (por defecto `on`).
   - **power**: sensor de consumo en W (enchufe Meross/Shelly/Tuya). Se avisa si supera
     el umbral configurado.

Cada vez que la alarma pase a "arming" o se arme directamente, la integración revisa
todas las entidades vigiladas y notifica si algo no cuadra. El estado de cada entidad
vigilada también se recalcula en vivo (no solo al armar), así que el mapa (ver abajo)
siempre refleja la situación actual. El `binary_sensor` de estado expone el detalle del
último chequeo en sus atributos.

## Plano de la vivienda

Desde las opciones de la integración → "Configurar plano" puedes:

- **Usar el mapa de tu robot aspirador**, si tu integración lo expone como entidad
  `camera` con el atributo `calibration_points` (Roborock, Valetudo, Xiaomi/Dreame...).
  Departure Guardian detecta automáticamente estas cámaras. **Eufy Robovac no expone
  este dato hoy**, así que no aparecerá en la lista si es tu único robot.
- **Subir un PNG** de tu plano (una foto, un plano escaneado, o una captura del mapa de
  la app de tu robot) como alternativa universal, funcione o no tu robot con HA.

Para colocar las entidades sobre el plano, añade la card personalizada a un dashboard:

```yaml
type: custom:departure-guardian-map-card
entity: binary_sensor.problema_al_salir   # el binary_sensor que crea la integración
```

En la card, pulsa "Editar posiciones", elige la entidad en el desplegable y haz clic
sobre el punto del plano donde está — se guarda al momento. Cada entidad se pinta como
un punto verde (todo bien) o rojo (problema detectado), actualizado en vivo.

## Licencia

MIT
