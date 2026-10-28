# Resolve Pro Pack

Paquete de recursos para DaVinci Resolve 20/21 **Studio** en Windows: transiciones, títulos, efectos y generadores de Fusion, más LUTs y DCTL de color. Todo lleva el prefijo `PRO_` y se agrupa en **PRO Pack** dentro de cada categoría de la Effects Library.

> **Estado:** las 51 plantillas de los lotes 1 a 7 cargan en Resolve 20.3 (comprobado en su registro: 422 plantillas en total, sin errores). Las de los lotes 8 a 10 pasan el validador pero aún no se han abierto en Resolve. El **aspecto visual** de cada pieza está sin revisar: hazlo con [CHECKLIST_PRUEBAS.md](CHECKLIST_PRUEBAS.md).

## Contenido

| Categoría | Cantidad | Ejemplos |
|---|---|---|
| Transiciones | 16 | Blur dissolve, zoom punch, zoom radial, whip pan, giro, remolino, barras, iris, light leak, film burn, glitch, salto de cinta, tira de película, quemado orgánico, empuje |
| Títulos y gráficos | 26 | Lower third, contador, barra de progreso, callout, end screen, suscríbete, cita, título de apertura, línea de tiempo, anillo giratorio, máquina de escribir, resaltador, texto con destello, neón, y 10 estilos de texto con su fuente (viral, gancho, trailer, elegante, minimal, documental, deportivo, retro 80, gamer, nota) |
| Efectos | 39 | Grano + halation, película completa (estilo Dehancer), proyector, lentes (anamórfico, vintage, lomo, flare), VHS, CRT, shake, punch-in, Ken Burns, letterbox, glow neón, duotono, halftone, sombra larga, animación de entrada/salida, pantalla dividida, cámaras (REC, seguridad, visión nocturna, térmica), rayos de luz, lluvia, nieve, eco, desenfoque de movimiento, reencuadre horizontal ↔ vertical, guía de zonas seguras, cámara digital Y2K |
| Generadores | 10 | Fondo con luz, cuadrícula, degradado animado, bokeh, aurora, fuga de luz, estática de TV, cuenta regresiva de película, brasas, synthwave |
| LUTs (.cube) | 8 | Teal & Orange, Frío Thriller, Film Suave, Película Print, B/N Contraste, Cozy Ámbar, Digicam Y2K, Limpio Luminoso |
| DCTL (Studio) | 1 | Teal & Orange con deslizadores |

La descripción y los controles de cada pieza están en [docs/preview.md](docs/preview.md). Las fuentes que necesitan los estilos de texto, y cómo trabajar en horizontal y vertical, están en [docs/fuentes.md](docs/fuentes.md).

## Instalar en una PC nueva

1. Instala Git para Windows: <https://git-scm.com/download/win>.
2. Abre PowerShell en la carpeta donde quieras guardar el paquete y descárgalo:
   ```powershell
   git clone https://github.com/Eduardo0719382/DavinciPro.git
   cd DavinciPro
   ```
3. Cierra DaVinci Resolve. Haz una simulación (no escribe nada) y luego instala:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```
4. Abre Resolve y busca **PRO Pack** en Edit › Effects › Toolbox.

Si el instalador avisa que no puede escribir en la carpeta LUT, vuelve a ejecutarlo en una PowerShell "Como administrador".

## Actualizar cuando haya cambios

En la carpeta `DavinciPro` de esa PC:

```powershell
powershell -ExecutionPolicy Bypass -File .\actualizar.ps1
```

Este script descarga los cambios de GitHub (`git pull`) y ejecuta el instalador. El instalador solo copia lo nuevo o modificado y hace backup de cualquier archivo que no sea del paquete. Si Resolve está abierto, normalmente detecta las plantillas nuevas solo; si no, reinícialo.

## Dónde se instala cada cosa

| Archivo | Ruta |
|---|---|
| `.setting` | `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit\{Transitions,Titles,Effects,Generators}\PRO Pack` |
| `.fuse` | `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Fuses` |
| `.cube` y `.dctl` | `%ProgramData%\Blackmagic Design\DaVinci Resolve\Support\LUT\PRO_Pack` |
| Manifiesto y backups | `%LOCALAPPDATA%\ResolveProPack` |

## Desinstalar

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Solo borra los archivos que siguen siendo idénticos a los instalados, y restaura los backups que hizo la instalación.

## Color con material de distintas cámaras

Los looks (`.cube` y `.dctl`) esperan una imagen **Rec.709 Gamma 2.4**. Con material log, pon primero un nodo Color Space Transform (cámara → Rec.709 / Gamma 2.4) y después el LUT. Para bajar la intensidad de un `.cube`, usa **Key Output Gain** en la pestaña Key del nodo.

## Para desarrollar

Las plantillas de los lotes 2 a 10 se generan con un script. Edita `tools/build_templates.py` (no los `.setting`) y regenera:

```powershell
python tools\build_templates.py   # regenera las plantillas generadas
python tools\generate_luts.py     # regenera los .cube
python tools\validate.py          # valida todo (.setting, .cube, .dctl)
```

Ver también: [DECISIONS.md](DECISIONS.md) · [CHECKLIST_PRUEBAS.md](CHECKLIST_PRUEBAS.md) · [QUIZ.md](QUIZ.md)
