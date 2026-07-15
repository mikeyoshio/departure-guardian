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
3. Desde las opciones de la integración, añade las entidades a vigilar:
   - **binary**: sensor on/off (horno, ventana, puerta). Se avisa si su estado coincide
     con el "estado problema" configurado (por defecto `on`).
   - **power**: sensor de consumo en W (enchufe Meross/Shelly/Tuya). Se avisa si supera
     el umbral configurado.

Cada vez que la alarma pase a "arming" o se arme directamente, la integración revisa
todas las entidades vigiladas y notifica si algo no cuadra. También expone un
`binary_sensor` de estado con el detalle del último chequeo en sus atributos.

## Licencia

MIT
