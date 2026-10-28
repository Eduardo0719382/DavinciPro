# Registro de decisiones

## D1. Lote piloto antes del catálogo completo
- **Elegido:** 6 piezas, una por cada tipo técnico (transición, título, efecto, generador, LUT y DCTL), que tú pruebas antes de producir el resto. Lo aprobaste en el discovery (opción 3a).
- **Considerado:** generar las ~70 piezas de una vez.
- **Por qué no:** no puedo abrir Resolve. Un error de patrón se repetiría en todas las piezas y obligaría justo a la ronda de "deshaz y prueba otra vez" que el objetivo cuenta como fallo.

## D2. Estructura copiada de las plantillas oficiales de Blackmagic
- **Elegido:** usar como referencia los ejemplos de `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Fusion Templates` (Noise Dissolve, Gradient, Rounded Window) que instala Resolve 20.3, y su README.
- **Por qué:** es la fuente más fiable disponible sin abrir Resolve. El validador se calibró con esas plantillas: pasan sin errores.

## D3. Animación con el modificador Anim Curves (`LUTLookup`) y expresiones
- **Elegido:** cada plantilla animada tiene un modificador `LUTLookup` (progreso 0→1 a lo largo del clip o la transición) conectado a un control "Progreso". Las demás animaciones son expresiones sobre ese valor (`sin`, suavizado smoothstep).
- **Considerado:** (a) keyframes fijos; (b) expresiones con `comp.RenderStart` y `comp.RenderEnd`.
- **Por qué:** el README oficial desaconseja los keyframes fijos porque no se adaptan a la duración. `LUTLookup` es el mecanismo documentado y es el que usa Noise Dissolve.
- **Consecuencia:** la entrada y la salida del lower third se expresan en **% de la duración del clip**, no en fotogramas.

## D4. Subcarpeta `PRO Pack` dentro de cada categoría, con prefijo `PRO_` (revisado a petición tuya)
- **Elegido:** copiar los `.setting` a `Templates\Edit\<Categoría>\PRO Pack\`, con el prefijo `PRO_` y un nombre por situación (`PRO_TTL_Corp_…`).
- **Límite de Resolve:** no existe una carpeta única que reúna transiciones, títulos, efectos y generadores. Resolve agrupa por tipo, y solo reconoce las plantillas dentro de `Edit\{Transitions,Titles,Effects,Generators}`. Lo más cercano es un grupo "PRO Pack" en cada tipo.
- **Versión anterior:** instalación plana directamente en la carpeta de categoría.
- **Considerado:** un paquete `.drfx` (un zip que Resolve instala con doble clic desde la versión 17.2).
- **Por qué:** pediste scripts con backup y control total. `.drfx` es una **alternativa mejor para distribuir** (un solo archivo, iconos incluidos), pero no tiene backup ni desinstalación granular. **Propuesta:** generar también un `.drfx` en el lote completo.

## D5. LUT y DCTL en `ProgramData\…\LUT\PRO_Pack`
- **Elegido:** una subcarpeta propia dentro de la carpeta LUT del sistema. Requiere administrador.
- **Por qué:** es la carpeta que muestra Resolve (Open LUT Folder), y la subcarpeta aísla el paquete. Sin permisos, el instalador avisa y omite esta parte en lugar de fallar.

## D6. Manifiesto con hash SHA-256
- **Elegido:** `%LOCALAPPDATA%\ResolveProPack\manifest.json`, fuera de las carpetas de Resolve.
- **Por qué:** permite desinstalar solo lo que sigue intacto, conservar lo que editaste y restaurar exactamente los backups. Probado en una carpeta simulada: instalar, reinstalar, editar, desinstalar y quedarse sin permiso de LUT.

## D7. Solo Windows: sin `install.sh` ni `uninstall.sh`
- **Elegido:** solo PowerShell, porque respondiste "Windows".
- **Contradicción con el brief:** la estructura pedía `install.sh`. Se añadirá si algún día necesitas macOS.

## D8. Looks diseñados para entrada Rec.709 Gamma 2.4
- **Elegido:** looks en espacio de visualización Rec.709, con un flujo documentado (CST antes del look) para tu material mixto.
- **Considerado:** looks nativos para DaVinci Wide Gamut / Intermediate.
- **Por qué:** un `.cube` Rec.709 sirve a cualquier flujo si se pone un CST delante. Uno en DWG fallaría en proyectos sin gestión de color. **Propuesta:** como tienes Studio, los DCTL del lote completo pueden incluir un selector "Espacio de entrada" (Rec.709 / DWG-Intermediate) que haga la conversión internamente.

## D9. El DCTL replica la matemática del LUT
- **Elegido:** la misma fórmula en `tools/generate_luts.py` y en el `.dctl`, con los mismos valores por defecto.
- **Por qué:** el `.cube` funciona en cualquier sitio; el DCTL añade deslizadores y precisión sin la interpolación de un LUT 33³.

## D10. Paleta neutra y fuente Arial
- **Elegido:** blanco, grises y un acento editable; fuente Arial (viene con Windows).
- **Por qué:** pediste un estilo neutro. No respondiste sobre fuentes, y si falta la fuente que pide una plantilla, Resolve la sustituye sin avisar.

## D11. Validador propio en Python
- **Elegido:** `tools/validate.py`, un parser del subconjunto Lua que usa Fusion, más comprobaciones de estructura (entradas según la categoría, SourceOp existentes, identificadores en expresiones), `.cube` y `.dctl`.
- **Verificación:** acepta las 3 plantillas oficiales y detecta 4 errores inyectados a propósito (SourceOp roto, coma faltante, función mal escrita, entrada principal faltante).
- **Límite:** no ejecuta Fusion. Valida la forma, no el resultado visual.

## D12. Lote 2 generado por script, no a mano
- **Elegido:** `tools/fusion_builder.py` + `tools/build_templates.py` generan las 10 plantillas nuevas.
- **Por qué:** si la checklist revela un error de patrón (por ejemplo, cómo se declara un control), se corrige en un único sitio y se regeneran todas. Escritas a mano, habría que tocar 10 archivos.
- **Riesgo aceptado a tu petición:** el lote se generó antes de que se probara el piloto. Reutiliza sus patrones, así que un fallo del piloto afectaría a estas piezas.
- **Evitado a propósito:** herramientas cuyos nombres de parámetros no puedo confirmar (DirectionalBlur, ChannelBooleans). El RGB split separa canales multiplicando por colores puros y recombinando en modo Screen, que es exacto para canales disjuntos.

## D13. Lentes: solo rasgos que se pueden simular de forma honesta
- **Elegido:** bloques reutilizables (aberración radial, bordes blandos, bloom, tono, dominante, viñeta) combinados en 5 lentes.
- **Descartado:** bokeh ovalado y swirl (requieren profundidad de escena) y distorsión de barril (los parámetros de LensDistort no se pueden confirmar sin Resolve).
- **Aberración cromática:** los canales R y B se escalan hacia fuera (>= 1) en lugar de uno hacia dentro, para no dejar franjas vacías en el borde del cuadro. A cambio, la franja es magenta/verde.
- **Alternativa comercial:** LensNode (Node Mill) usa perfiles medidos de lentes reales. Es la opción si necesitas emular una lente concreta.

## D14. Réplicas de plugins de pago: función sí, marca no
- **Elegido:** reproducir las funciones más citadas (Dehancer: gate weave, respiración, daño, formato; Sapphire: lens flare, glitch; Universe: VHS) con nodos nativos y nombres propios del paquete.
- **Descartado:** Neat Video (reducción de ruido por perfil; Resolve Studio ya trae NR temporal), PixelSort (necesitaría un Fuse) y "pelos" en el daño de película (formas dibujadas).
- **"Formato (mm)":** una sola expresión (35/Formato) escala el weave y la respiración, y otra más suave escala el grano. Es la idea de los perfiles por formato de Dehancer, sin sus mediciones.

## D15. Transiciones de cinta
- **Daños escalados por una campana:** sin(π·progreso) hace que los daños sean máximos en el centro y nulos en los extremos, para que los clips entren y salgan limpios.
- **Perforaciones:** 17 máscaras por lado encadenadas por `EffectMask` (un solo Background por lado) en lugar de 34 fondos y 34 merges, por rendimiento. Riesgo: el encadenado de máscaras no está confirmado (checklist 10.3).
- **Quemado orgánico:** umbral móvil sobre FastNoise (Low = 1 − 0.9·quemado·campana). Las manchas crecen sin necesidad de dibujar formas.

## D16. Lote 6: técnicas de la clase de reels
- **Fuente:** la transcripción de la clase (YouTube, Lorenzo). Del short "efectos épicos" no se pudo extraer contenido: no tiene subtítulos y las capturas fallaron con el panel del navegador oculto.
- **Patrones:** rejillas a partir de gradientes "Ping-Pong" con umbral (cuadrícula y halftone); dirección de movimiento por ángulo con corrección de aspecto; rebote con easeOutBack.
- **Descartado:** el texto palabra por palabra (requiere un Follower de Text+ sin sintaxis confirmada) y los objetos 3D (requieren modelos y cámara 3D).

## D17. Lote 7: sistema común para títulos
- **Elegido:** `kit()` + `stage()`. Cada título tiene un avance de entrada U (0..1) y un factor de salida Xs; cada elemento aparece en su propia fase (a..b) de la entrada. Así los títulos se escalonan sin keyframes y se adaptan a cualquier duración.
- **Contador:** el texto se genera con una expresión `Text(string.format(...))` en StyledText. Riesgo: checklist 12.1.
- **Mezclas de dos colores** (duotono, degradado): A·(1−x) + B·x mediante el modo aditivo del Merge, el mismo riesgo que el halftone.
- **Bokeh:** 14 luces con su propio fondo y máscara, sin máscaras encadenadas, para que funcione aunque el encadenado falle. Las posiciones son pseudoaleatorias con semilla fija, así que salen igual cada vez.

## D18. Lote 8: solo herramientas que ya usa el paquete
- **Elegido:** 18 piezas (4 títulos de texto, 4 transiciones, 10 efectos) construidas únicamente con las herramientas de los lotes anteriores: Transform, Blur, BrightnessContrast, Merge, Background, FastNoise, máscaras y Text+.
- **Desenfoque radial sin herramienta propia:** `ZoomRadial` y `Luz_Rayos` promedian varias copias escaladas (cada Merge con mezcla 1/(k+1)). Para escalar desde un punto O sin usar Pivot, el centro de cada copia es 0.5 + (O − 0.5)·(1 − escala).
- **Máquina de escribir:** un Text+ oculto guarda la frase y el visible la recorta con `string.sub`. Riesgos: leer `StyledText.Value` de otro nodo y que Lua cuente bytes (una tilde puede verse mal durante un fotograma).
- **Pantalla dividida:** un efecto por clip con su celda, en lugar de una plantilla de varias entradas: en la página Edit un efecto solo recibe el clip al que se aplica.
- **Grupos de controles:** el nuevo `numbered()` calcula `ControlGroup` a partir de nombres simbólicos, para no contar a mano la posición de cada selector de color.
- **Descartado:** caleidoscopio y espejo (el modo de bordes de Transform no se puede confirmar), eco o estela (las herramientas de tiempo no se pueden confirmar), pixelado (Resolve ya trae Mosaic), audio-reactivo (las plantillas de Edit no reciben audio), ruta de mapa y gráficos de datos (para un lote propio).

## D19. Lote 9: las plantillas oficiales como referencia de parámetros
- **Fuente:** las plantillas que trae Resolve (`Program Files\…\Fusion\Templates\Templates.drfx`). Se leyeron sin modificarlas para confirmar nombres de parámetros que no se podían probar.
- **Confirmado gracias a ellas:** los elementos de sombreado de Text+ (contorno `Enabled2`/`Thickness2`/`OutsideOnly2`, sombra suave `Enabled8`/`SoftnessX8`/`Offset8`, caja `ElementShape = 2` + `Level = 1` + `ExtendHorizontal`/`ExtendVertical`), `CharacterSpacing` y las entradas de `TimeSpeed` (`Speed`, `Delay`), `DirectionalBlur` (`Length`, `Angle`) y `Vortex` (`Size`, `Angle`). La incógnita 12.2 (`CharacterSpacing`) queda resuelta.
- **No duplicar lo que Resolve ya trae:** Resolve incluye CCTV, Night Vision, Video Camera, Crash Zoom, Spin y unos 20 estilos de subtítulos, entre ellos "Word Highlight" (palabra por palabra). El lote 9 se centra en lo que falta: estilos con su fuente, reencuadre horizontal ↔ vertical, zonas seguras, eco y looks.
- **Fuentes de Google Fonts (OFL) o de Windows, no comerciales:** el equipo tiene fuentes de pago o demo (Obviously, Integral CF, Futura Now). Se evitaron para que el paquete funcione en otra PC instalando solo fuentes gratuitas. Lato se cambió por Montserrat Light porque en este equipo está instalada como varias familias separadas ("Lato-Light"), y su nombre en Text+ es dudoso.
- **Formato vertical:** una casilla mueve y escala el bloque completo. Las fuentes se miden respecto al ancho del cuadro, así que en 9:16 un texto ocupa el mismo porcentaje de ancho que en 16:9; la casilla lo saca de las zonas que tapa la interfaz.
- **Investigación de tendencias:** CapCut (velocity edits, glitch, slow zoom) y Opus (11 estéticas de 2026: cozy/flat-lay, phone-first cinematic, video ensayo, UGC). Los nombres de fuentes vienen de guías de miniaturas y subtítulos (Montserrat, Anton, Bebas Neue, Poppins, Roboto).

## D20. Lote 10: generadores y menos ruido en CintaPelicula
- **CintaPelicula:** los daños bajan de 1 a 0.35 y el parpadeo de 0.4 a 0.2 (lo pediste: "disminuir el ruido"). Se añade la misma fuga de luz que `PRO_TR_LightLeak` (dos óvalos de color en Screen que cruzan la imagen), con su control y colores.
- **Generadores elegidos:** los recursos más ofrecidos en los bancos de stock son las fugas de luz, las colas de película (countdown), las escenas synthwave y los degradados aurora o de malla. Se añadieron, junto con estática de TV y brasas, que son los fondos y overlays más comunes en intros y transiciones.
- **Rejilla synthwave sin atan:** las expresiones de Fusion no tienen `atan`. Los ángulos y largos de las 15 líneas verticales se calculan en el script para 16:9 y 9:16, y una casilla elige entre los dos.
- **Overlays sobre negro:** FugaLuz y Brasas salen sobre negro opaco en lugar de transparentes, para que el modo Screen o Add de la pista los combine sin depender del canal alfa.

## D21. Lote 11: ritmo por BPM en lugar de marcadores
- **Elegido:** los efectos al ritmo calculan el golpe con BPM, FPS y un desfase en fotogramas.
- **Por qué:** las plantillas de la página Edit no leen el audio ni los marcadores de la timeline. Con BPM + desfase, un solo Adjustment Clip sigue toda una canción de tempo fijo.
- **Límite:** las canciones con tempo variable desfasan con el tiempo. En ese caso, corta el Adjustment Clip y reajusta el desfase en cada tramo.
- **Clones:** usa el modo de bordes de Transform. `Edges = 1` aparece en las plantillas oficiales; que 1 sea Wrap y 3 sea Mirror es una suposición (checklist 16.5).
- **Fuentes de la investigación:** las guías de 2026 coinciden en editar al ritmo (cortes, zooms, flashes y sacudidas en los golpes), en los velocity edits y en el glitch. No hay datos fiables sobre impact frames ni antes/después; se incluyen porque son formatos muy comunes en shorts.

## D22. Comentario con foto como efecto, no como título
- **Elegido:** `PRO_FX_Social_ComentarioFoto` es un efecto que se aplica a la foto puesta en la timeline. Usa el clip como avatar y dibuja la burbuja; el resto queda transparente.
- **Considerado:** un título con un Loader y el campo "Image File", como hacen las plantillas oficiales de Resolve.
- **Por qué no:** el Loader necesita una imagen por defecto que el instalador tendría que copiar en una subcarpeta. Además, el tamaño de la foto cargada depende de su resolución y no se puede encajar en el círculo sin probarlo. Con el efecto, Resolve entrega la foto ya ajustada al cuadro y el recorte es predecible. Si quieres el campo para elegir archivo, se puede intentar en otra versión.
- **Transiciones del lote 12:** las guías de 2026 destacan el glitch, la distorsión digital, el zoom y el "masking". Se eligieron variantes que Resolve no trae: destello de lente, zoom a través de un punto, cambio de canal, apagón y corte diagonal.

## D23. Lote 13: iconos con formas y comentario medido en una sola unidad
- **Comentario:** en tu captura el avatar se salía de la caja. La caja (RectangleMask) y el avatar (EllipseMask) no se ven en la misma escala, y los textos estaban a alturas fijas en coordenadas del cuadro. Ahora el avatar es un RectangleMask con las esquinas al máximo (círculo) del mismo tipo que la caja. La caja mide avatar + dos márgenes. Las alturas de los textos se convierten con el aspecto que marca "Formato vertical". Por eso el control "Aspecto" del comentario con foto pasa a ser esa casilla.
- **Iconos sin imágenes:** se dibujan con RectangleMask (círculos con esquinas al máximo, rombo girado) y TriangleMask (parámetros `Point1-3` copiados de las plantillas oficiales). Así no dependen de archivos externos ni de fuentes de iconos. La excepción son las estrellas: el carácter ★ de Segoe UI Symbol viene con Windows y una estrella de 5 puntas no se puede dibujar con estas máscaras.
- **Unidad común:** posiciones y tamaños de los iconos en unidades del ancho del cuadro; las alturas se multiplican por el aspecto (16:9 o 9:16 según la casilla). Las formas no se deforman al cambiar de formato.

## D24. Unidad real del alto de RectangleMask (corrección de formas)
- **Hallazgo:** tus capturas del comentario y del corazón muestran que `RectangleMask.Height` es una fracción del **alto** del cuadro, no del ancho. Un rectángulo con Width = Height = 0.064 sale 16:9 veces más ancho que alto en una timeline horizontal: el avatar "aplastado" y el corazón deformado.
- **Corrección:** todo alto que se quería en unidades del ancho se multiplica por el aspecto (W/H). En las piezas con "Formato vertical" se usa la casilla; en los títulos del lote 7 y `Texto_Resaltado`, pensados para 16:9, se usa 16/9. Donde el alto era "una fracción del cuadro" (barras, tarjeta, pantalla CRT, zonas seguras, celdas de la pantalla dividida, contenido del reencuadre, suelo synthwave), ahora se da directamente y sobra el control "Aspecto" en Tarjeta, Barras, CRT y Zonas seguras.
- **Piezas corregidas:** comentario (título y con foto), los 8 iconos, Tarjeta, Barras, REC, CRT, Pantalla dividida, Reencuadre, Zonas seguras, Synthwave, Corte, Barra de progreso, Callout, End screen, Suscríbete, Cita, Título de apertura, Separador, Línea de tiempo, Anillo giratorio, Texto resaltado, Elegante, Deportivo y Nota.
- **EllipseMask no cambia:** en la primera captura el avatar (una elipse con Width = Height) salió redondo, así que su alto ya va en unidades del ancho. Los círculos nuevos se dibujan igualmente con RectangleMask (esquinas al máximo) para usar una sola regla.

## D25. Revisión en horizontal y vertical: el texto se mide sobre el alto
- **Hallazgo:** en Fusion, el tamaño de Text+ también es una fracción del **alto** del cuadro (las capturas del comentario lo confirman: la altura del texto sigue a la de la caja). En 9:16 el alto es 3.16 veces mayor respecto al ancho, así que cualquier título diseñado en 16:9 salía con el texto 3.16 veces más grande que sus formas, y se desbordaba o tapaba los elementos.
- **Corrección general:** todos los títulos tienen "Formato vertical (9:16)". Al marcarlo, `vertical_map()` multiplica por K = 0.3164 los tamaños de texto, los altos de rectángulo y la distancia vertical al centro. Así el título se ve **idéntico** al de 16:9, escalado al ancho. Luego `Formato` lo agranda (entre 1.2 y 2.5 según la pieza, para que ocupe bien el ancho sin salirse) y lo coloca fuera de las zonas que tapa la interfaz. Los tamaños de texto pasan a controles del título, así que siguen siendo editables en el Inspector.
- **Efectos con texto:** REC (con su control de aspecto), Cámara de seguridad, Digicam, Cuenta regresiva, Antes/Después y Texto Pop reducen el texto en vertical; los que no tenían casilla la incorporan.
- **Rótulo deportivo:** el dato era rojo sobre la barra roja y la barra lo tapaba. Ahora la barra es más baja (cabe justo el nombre), el dato va en blanco debajo y tiene su propio color y fuente en el Inspector.
- **Sin casilla vertical:** `Callout_Flecha` (su posición la marca el punto que arrastras, que no se puede recalcular sin romper ese control) y el lower third del piloto, escrito a mano.
