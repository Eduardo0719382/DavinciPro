# Descripción y uso de cada pieza

Todas las piezas están **sin probar en Resolve**. Los controles indicados son los que aparecen en el Inspector de la página Edit.

---

## PRO_TR_BlurDissolve_Flash — Transición
**Para qué:** cambio de escena suave con desenfoque. Con un toque de flash sirve para cortes de ritmo, bodas o eventos.
**Cómo funciona:** los dos clips se desenfocan (al máximo a mitad de la transición), se funden con una curva suave y, si lo activas, un destello breve aparece en el punto medio.
**Uso:** arrástrala a un punto de corte. Su duración se cambia en la timeline, y la animación se adapta sola.

| Control | Por defecto | Notas |
|---|---|---|
| Desenfoque | 25 | 0 = disolución limpia; 40-60 = más soñador |
| Flash (intensidad) | 0 | 0.3-0.6 = destello visible; 1 = blanco total en el medio |
| Color del flash | blanco | Prueba un ámbar cálido para un look de película |

---

## PRO_TTL_Corp_LowerThird — Título
**Para qué:** nombre y cargo en entrevistas, vídeos corporativos o documentales.
**Diseño:** una barra vertical fina de acento, el nombre en negrita y el cargo más pequeño y en gris claro. Entra con un deslizamiento suave hacia la derecha y la barra crece; al final sale invirtiendo la animación.
**Uso:** arrástralo a una pista por encima del vídeo. Recomendado: 4-7 s.

| Control | Por defecto |
|---|---|
| Nombre / Cargo | "Nombre Apellido" / "Cargo · Empresa" |
| Fuente del nombre / del cargo | Arial Bold / Arial Regular |
| Color del nombre / del cargo / de la barra | blanco / gris 82 % / blanco |
| Posición / Escala | centro / 1.0 (mueve todo el bloque) |
| Duración entrada / salida | 15 % / 12 % de la duración del clip |

*Diseñado para 16:9. Las versiones 9:16 llegarán en el lote completo.*

---

## PRO_FX_Cine_GranoHalation — Efecto
**Para qué:** dar textura de película a material digital "demasiado limpio".
**Cómo funciona:** extrae las luces altas, las desenfoca, las tiñe de rojo-anaranjado y las suma en modo Screen (halation). Encima añade grano animado en modo Overlay.
**Uso:** aplícalo a un clip, o a un **Adjustment Clip** para que afecte a toda la secuencia que tenga debajo.

| Control | Por defecto | Notas |
|---|---|---|
| Halation (cantidad) | 0.35 | 0 la desactiva |
| Halation (umbral de luces) | 0.75 | Más bajo = afecta a más zonas |
| Halation (radio) | 30 | Más alto = más difuso |
| Halation (color) | rojo-naranja | |
| Grano (cantidad) | 0.12 | 0.05 sutil, 0.25 marcado |
| Grano (finura) | 40 | Comprueba en Resolve si más alto da grano más fino |
| Grano (contraste) | 1.5 | |

---

## PRO_GEN_Fondo_Luz — Generador
**Para qué:** un fondo elegante en movimiento para títulos de apertura, end screens o citas.
**Cómo funciona:** sobre un fondo oscuro, una luz difusa se desplaza lentamente en órbita, con una textura de grano muy sutil.

| Control | Por defecto |
|---|---|
| Color de fondo | gris casi negro |
| Color de la luz | gris azulado |
| Intensidad / Suavidad de la luz | 0.85 / 0.35 |
| Movimiento (vueltas por clip) | 1 (0 = estático) |
| Textura (grano) | 0.05 |

---

## PRO_Look_TealOrange.cube — LUT
**Para qué:** el look cinematográfico clásico: piel cálida, sombras y fondos hacia el cian, contraste en S suave.
**Entrada:** Rec.709 Gamma 2.4 (lee "Color con material de distintas cámaras" en el README).
**Uso:** página Color › nodo › clic derecho › LUT › PRO_Pack. Intensidad: Key Output Gain.

## PRO_TealOrange.dctl — DCTL (solo Studio)
La misma matemática que el `.cube`, con deslizadores: **Intensidad** (0-1.5), **Contraste**, **Tonificado sombras-altas** y **Empuje eje piel-cian**.
**Uso:** nodo › ResolveFX › DCTL › elegir `PRO_TealOrange`.

---

# Lote 2: dinámico y cine

Generado por `tools/build_templates.py`. Todo **sin probar en Resolve**.

## Efectos (Edit › Effects › Toolbox › Effects › PRO Pack)

### PRO_FX_Din_PunchIn: zoom de golpe
Para jump cuts y para remarcar frases en vlogs y reels. El zoom entra rápido al principio del clip y se mantiene.
| Control | Por defecto | Notas |
|---|---|---|
| Zoom extra | 0.15 | 0.1 sutil, 0.3 fuerte |
| Centro del zoom | centro | Ponlo en la cara |
| Duración entrada | 8 % | 1 % = corte instantáneo |
| Duración salida | 0 % | 0 = no vuelve a su tamaño |

### PRO_FX_Din_Shake: sacudida de cámara
Para impactos, golpes de música y acción. Usa un movimiento orgánico (suma de ondas), con zoom automático para que no se vean los bordes.
| Control | Por defecto | Notas |
|---|---|---|
| Intensidad | 0.3 | |
| Velocidad | 1 | |
| Rotación | 0.3 | 0 = solo desplazamiento |
| Decaimiento | 0 | 1 = fuerte al inicio y se calma (ideal para impactos) |

### PRO_FX_Din_RGBSplit: aberración cromática / glitch RGB
Para videoclips, eventos e intros. Separa los canales rojo y azul.
| Control | Por defecto | Notas |
|---|---|---|
| Separación | 0.006 | 0.02 o más = glitch evidente |
| Ángulo | 0° | 90 = vertical |
| Pulso glitch | 0 | Hace que la separación lata de forma irregular |
| Velocidad del pulso | 1 | |
| Mezcla con el original | 1 | |

### PRO_FX_Din_FlashBeat: flash al ritmo
Ponlo en el clip que empieza justo en el golpe de música: un destello y una subida de exposición que se apagan rápido.
| Control | Por defecto |
|---|---|
| Intensidad del flash | 0.8 |
| Duración | 12 % del clip |
| Color del flash | blanco |
| Golpe de exposición | 0.3 |

### PRO_FX_Cine_Letterbox: barras de cine animadas
Úsalo sobre un **Adjustment Clip** para que afecte a toda la secuencia. Las barras entran animadas.
| Control | Por defecto | Notas |
|---|---|---|
| Aspecto destino | 2.39 | 2.0, 1.85… |
| Aspecto del timeline | 1.778 | **Cámbialo si tu timeline no es 16:9**: 9:16 = 0.5625, DCI 4K = 1.896 |
| Duración entrada / salida | 10 % / 0 % | Entrada 0 = barras fijas |
| Color de las barras | negro | |

### PRO_FX_Cine_Vineta: viñeta
Oscurece los bordes para llevar la mirada al centro. Controles: Intensidad 0.5, Suavidad, Ancho, Alto, Centro y Color.

### PRO_FX_Cine_Difusion: difusión tipo filtro "mist"
Un brillo suave alrededor de las luces, detalle menos digital y negros ligeramente levantados.
| Control | Por defecto |
|---|---|
| Brillo en altas luces | 0.45 |
| Umbral de altas luces | 0.6 |
| Radio del brillo | 60 |
| Suavizado del detalle | 0.25 |
| Negros levantados | 0.02 |

## Transiciones (Edit › Effects › Toolbox › Video Transitions › PRO Pack)

### PRO_TR_ZoomPunch: zoom de entrada
El clip A hace zoom hacia dentro, se corta en el centro y el clip B sale del zoom hasta su tamaño normal. Duración ideal: 8-16 fotogramas. Controles: Zoom (1 = el doble) y Desenfoque.

### PRO_TR_WhipPan: barrido rápido (swish)
El clip A sale disparado de lado con desenfoque de movimiento y entra el clip B. Duración ideal: 6-12 fotogramas.
| Control | Por defecto | Notas |
|---|---|---|
| Dirección | 1 | -1 = al lado contrario |
| Barrido vertical | no | |
| Desenfoque de movimiento | 80 | |

### PRO_TR_LightLeak: fuga de luz
Dos manchas de luz cálida cruzan la imagen mientras se funden los clips. Muy usada en bodas, viajes y recuerdos. Controles: Intensidad de la fuga, Color principal y Color secundario.

## Looks de color (página Color › LUTs › PRO_Pack)
- **PRO_Look_FrioThriller.cube**: contraste alto, saturación contenida, sombras verde-azuladas. Para thriller, tensión o noche urbana.
- **PRO_Look_FilmSuave.cube**: negros levantados, altas luces suaves, calidez ligera. Para documental, bodas o nostalgia.

---

# Lote 3: simulación de lentes

Basado en los rasgos que describen las fuentes consultadas: RED (anamórficos), reseñas del Helios-44 (vintage) y el plugin LensNode (coma, bloom, aberración cromática, viñeta y dominante de color). Todo **sin probar visualmente en Resolve**. Resolve sí las cargó: su registro pasó a 390 plantillas.

**No incluido, a propósito:** el bokeh ovalado y el swirl del Helios. Dependen de qué parte de la imagen está desenfocada, y una macro no conoce la profundidad de la escena. Una imitación sin esa información quedaría falsa.

### PRO_FX_Lente_Anamorfico
Destellos horizontales azulados en las fuentes de luz, estiramiento y blandura en los laterales, dominante fría ligera y viñeta. Queda mejor con luces puntuales (farolas, faros, velas) y con `PRO_FX_Cine_Letterbox` encima.
| Control | Por defecto |
|---|---|
| Destellos: intensidad / umbral / longitud / color | 0.6 / 0.85 / 400 / azul |
| Estiramiento en laterales | 18 |
| Dominante fría | 1 |
| Viñeta | 0.3 |

### PRO_FX_Lente_Vintage (carácter tipo Helios / óptica antigua)
Bajo contraste, negros levantados, esquinas blandas, halo cálido en las luces, aberración cromática en los bordes, calidez y viñeta.

### PRO_FX_Lente_Lomo (cámara de juguete)
Saturación y contraste altos, viñeta fuerte, esquinas muy blandas y aberración marcada.

*Vintage y Lomo comparten controles:* Aberración cromática, Esquinas blandas, Halo en luces, Contraste, Negros levantados, Saturación, Dominante de color (cantidad y color) y Viñeta.

### PRO_FX_Lente_AberracionRadial
Solo la franja de color (magenta/verde) en los bordes, que crece desde el centro como en una lente real. Control: Intensidad (2 por defecto).

### PRO_FX_Lente_TiltShift (efecto maqueta)
Una franja enfocada y el resto desenfocado, con más saturación. Funciona mejor en planos aéreos o picados.
| Control | Por defecto |
|---|---|
| Posición de la franja enfocada | ligeramente bajo el centro |
| Ancho de la franja / Transición / Ángulo | 0.15 / 0.12 / 0° |
| Desenfoque | 25 |
| Saturación (efecto maqueta) | 1.3 |

---

# Lote 4: al estilo de los plugins de pago

Réplicas aproximadas de las funciones más citadas de Dehancer Pro, Boris FX Sapphire y Red Giant Universe. **No son los plugins originales:** reproducen la idea con herramientas nativas de Fusion. Resolve las cargó (396 plantillas); su aspecto está **sin revisar visualmente**.

### PRO_FX_Film_Completo (estilo Dehancer)
Pila completa de película: gate weave, respiración, halation, bloom, grano y viñeta. El control **Formato (mm)** escala el grano, el vaivén y la respiración como lo haría una película real: en 8 mm todo es más evidente; en 65 mm, casi imperceptible.
| Control | Por defecto |
|---|---|
| Formato (mm) | 35 |
| Grano / Halation / Bloom | 0.1 / 0.3 / 0.2 |
| Color de halation | rojo-naranja |
| Gate weave / Respiración / Viñeta | 1 / 1 / 0.25 |

### PRO_FX_Film_Proyector (estilo Dehancer: film damage)
Gate weave, respiración, polvo (motas que cambian en cada fotograma) y rayas verticales intermitentes. Combínalo con `Film_Completo` o con `GranoHalation`.
*No incluye "pelos": necesitan formas dibujadas que no se generan de forma creíble con ruido.*

### PRO_FX_Lente_Flare (estilo Sapphire LensFlare)
Núcleo de luz, raya anamórfica y 4 "fantasmas" de colores alineados a través del centro de la imagen, como en un objetivo real.
- **Para animarlo:** pon keyframes en **"Posición del destello"** en el Inspector, siguiendo el sol o un foco. Los fantasmas se mueven solos en la dirección opuesta.
- **Otros controles:** Intensidad, Tamaño y Color del núcleo, Raya anamórfica y su color, y la intensidad de cada fantasma.

### PRO_FX_Retro_VHS (estilo Red Giant Universe)
Temblor horizontal, corrimiento de color, separación RGB, negros levantados, ruido y una banda de tracking que recorre la imagen.

### PRO_TR_Glitch (transición)
Hacia el centro, la imagen salta entre los dos clips con separación RGB y franjas horizontales desplazadas. Duración ideal: 8-15 fotogramas.

### PRO_TR_FilmBurn (transición)
Quemado de película: una mancha naranja con núcleo blanco crece desde "Origen del quemado" mientras la imagen se sobreexpone y cambia de clip. Duración ideal: 20-40 fotogramas.

### LUTs
- **PRO_Look_PeliculaPrint.cube**: estilo copia de proyección. Pie y hombro suaves, densidad en rojos, sombras cian-verdosas y altas cálidas.
- **PRO_Look_BN_Contraste.cube**: blanco y negro con mezcla tipo filtro naranja (cielos más oscuros, piel limpia).

### Lo que no se puede replicar
- **Neat Video (reducción de ruido):** usa la Noise Reduction temporal de Resolve Studio (página Color › Motion Effects).
- **PixelSort de Sapphire:** requiere procesar píxeles de forma no lineal, algo que no se puede hacer con nodos de Fusion; haría falta un Fuse.
- **Perfiles medidos de película de Dehancer:** nuestros looks son aproximaciones artísticas, no mediciones de stocks reales.

---

# Lote 5: transiciones de cinta y daños

Todas incluyen **"Daños de película"** (0-3): polvo, rayas, vaivén y parpadeo, más intensos en el centro de la transición y limpios al principio y al final. Sin revisar visualmente en Resolve.

### PRO_TR_SaltoCinta (el fotograma se escapa)
Como cuando la película se sale del arrastre del proyector: el clip A sube, se ve la línea negra entre fotogramas y entra el clip B, con desenfoque vertical y parpadeo. Duración ideal: 8-15 fotogramas.
| Control | Por defecto |
|---|---|
| Línea de fotograma | 0.08 |
| Desenfoque de arrastre | 60 |
| Dirección | 1 (arriba) / -1 (abajo) |
| Daños de película | 1 |

### PRO_TR_CintaPelicula (tira de película con perforaciones)
La imagen se aleja y deja ver la tira de película con sus perforaciones iluminadas. La cinta avanza un fotograma y vuelve a acercarse en el clip B, mientras una fuga de luz cálida la cruza. Duración ideal: 20-40 fotogramas.
Controles: Alejamiento (0.3), Daños de película (0.35: polvo, rayas y parpadeo suaves), Color de la luz en perforaciones, Fuga de luz (0.7) y sus dos colores.

### PRO_TR_QuemaOrganica (quemado con formas irregulares)
Manchas de quemado con bordes naranjas y núcleo blanco que nacen del ruido y crecen hasta cubrir la imagen. Mientras tanto, la imagen se sobreexpone, vibra y se llena de polvo y rayas. Duración ideal: 20-45 fotogramas.
Controles: Intensidad del quemado, Daños de película, Color del borde quemado, Tamaño de las manchas.

### PRO_TR_FlashFotogramas (final de rollo)
Parpadeo rápido entre los dos clips, con fotogramas sobreexpuestos, saltos verticales y daños. Duración ideal: 10-20 fotogramas.
Controles: Destellos, Saltos de fotograma, Daños de película.

**Combinación recomendada:** pon `PRO_FX_Film_Completo` sobre un Adjustment Clip que cubra la secuencia, para que las transiciones y los planos compartan el mismo grano y halation.

---

# Lote 6: reels y redes (inspirado en una clase de edición viral)

Versiones propias de las técnicas de la clase "Cómo editar reels virales en DaVinci Resolve" (Lorenzo). No copian los plugins de pago que aparecen en ella (FlowShift, Deep Shadow, Halftone, Magic Animate): reproducen la idea con nodos nativos. Resolve las cargó (407 plantillas); su aspecto está **sin revisar visualmente**.

> **Formato vertical:** varias piezas tienen "Aspecto del timeline" con 0.5625 por defecto (9:16). En una timeline 16:9, cámbialo a 1.778.

### PRO_FX_Social_SombraLarga
Sombra larga direccional para PNG recortados (productos, objetos). Combínala con el efecto Blanco y Negro de Resolve para el look de la clase.
Controles: Ángulo (-45° = luz desde arriba a la izquierda), Longitud, Decaimiento, Opacidad, Suavidad.

### PRO_FX_Social_Halftone
Trama de puntos de cómic o periódico que crecen en las zonas oscuras. Controles: Tamaño de la trama, Intensidad, Saturación (0 = B/N), Umbral.

### PRO_FX_Anim_Flow
Animación de entrada o salida para cualquier clip o PNG, sin keyframes. Se adapta a la duración del clip.
| Control | Por defecto | Notas |
|---|---|---|
| Modo salida | no | Marca la casilla para animar la salida |
| Duración | 25 % del clip | |
| Dirección | 180° | Desde la izquierda; 90 = desde arriba, -90 = desde abajo |
| Distancia | 0.6 | |
| Zoom | 0 | -1 = "pop" desde 0; 0.5 = entra desde grande |
| Giro | 0° | |
| Rebote | 1 | 0 = sin rebote |
| Desenfoque de movimiento / Fundido | 15 / 0 | |

**Truco de la clase:** corta el clip y pon `Anim_Flow` en el primer trozo para la entrada y otro en el último trozo, con "Modo salida", para la salida.

### PRO_TR_Empuje (transición)
La escena A sale empujada y entra la B, con desenfoque de movimiento y picos de glow y flash en el centro, como las "middle curves" de la clase.
Controles: Dirección X / Y (-1, 0, 1), Desenfoque, Glow, Flash.

### PRO_TTL_Social_AnilloGiratorio (título)
Anillo de 24 guiones que gira sin parar, para poner detrás de un producto. Gira en función del tiempo, así que puedes alargar el clip sin keyframes.
Controles: Radio, Velocidad (negativa = sentido contrario), Largo y Grosor del guion, Color, Posición.

### PRO_GEN_Social_Cuadricula (generador)
Fondo de papel cuadriculado que se desvanece en los bordes.
Controles: Tamaño de celda, Grosor de línea, Colores, Intensidad, Desvanecido, Ancho y Alto visibles.

### PRO_TTL_Social_TextoPop (título)
Texto que entra con rebote mientras sube y aparece, y sale al revés.
Controles: Texto, Fuente, Tamaño, Color, Posición, Rebote, Duraciones.
*La animación palabra por palabra o letra por letra no está incluida: necesita el modificador "Follower" de Text+, que no puedo configurar sin probarlo en Resolve.*

---

# Lote 7: animaciones gráficas, generadores y efectos

Resolve las cargó (422 plantillas); su aspecto está **sin revisar visualmente**. Todos los títulos tienen **Posición**, **Escala** y **Duración de entrada/salida** (en % del clip). Sus elementos aparecen escalonados, no todos a la vez. Están diseñados para 16:9 salvo que se indique otra cosa.

## Animaciones gráficas (Titles › PRO Pack)

| Pieza | Para qué | Controles principales |
|---|---|---|
| `PRO_TTL_Barra_Progreso` | Barra que se llena durante el clip (tutoriales, cuenta atrás, retención en YouTube). **Alarga el clip y la barra tarda más.** | Colores de pista y relleno, ancho, grosor, altura en pantalla, redondeo |
| `PRO_TTL_Contador` | Número que cuenta de un valor a otro con frenada suave (seguidores, ventas, años) | Valor inicial y final, duración del conteo, fuente, colores, etiqueta |
| `PRO_TTL_Callout_Flecha` | Punto con aro, línea que crece y texto, para señalar algo en pantalla | Punto señalado (arrástralo en el visor), ángulo, largo, texto, color |
| `PRO_TTL_EndScreen` | Pantalla final de YouTube: título, dos marcos de vídeo, círculo del canal y texto | Título, texto inferior, fuente, colores |
| `PRO_TTL_Suscribete` | Botón rojo con rebote y un "clic" en la mitad del clip | Texto, colores, rebote |
| `PRO_TTL_Cita` | Cita para documental: comillas grandes, frase en cursiva, raya y autor | Frase, autor, fuente, tamaño, color de acento |
| `PRO_TTL_Titulo_Apertura` | Título de película: las letras se juntan mientras aparecen, con líneas finas arriba y abajo | Título, subtítulo, fuente, tamaño, color, separación inicial |
| `PRO_TTL_Separador` | Línea que crece desde el centro con puntos en los extremos y texto opcional | Texto, largo, colores |
| `PRO_TTL_LineaTiempo` | Línea de tiempo con 5 hitos que aparecen uno a uno, con año y texto | Año 1-5, Texto 1-5, color de los hitos |

## Generadores (Generators › PRO Pack)

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_GEN_Degradado_Animado` | Degradado de dos colores que gira lentamente; fondo moderno para títulos y reels | Color A, Color B, giro, ángulo inicial, textura, saturación |
| `PRO_GEN_Bokeh` | 14 luces desenfocadas que flotan despacio; fondo de intros y bodas | Color de fondo, Colores A/B, intensidad, velocidad, desenfoque |

## Efectos (Effects › PRO Pack)

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_FX_Duotono` | La imagen en dos colores (sombras y luces), estilo póster o Spotify | Color de sombras, Color de luces, contraste, mezcla |
| `PRO_FX_Glow_Neon` | Brillo intenso de luces de neón, con un halo cercano y otro amplio | Umbral, brillo cercano, halo amplio, radios, saturación |
| `PRO_FX_Polvo_Flotante` | Partículas de polvo en el aire, en dos capas de profundidad (rayos de luz, interiores) | Cantidad, brillo, velocidad, desenfoque |
| `PRO_FX_Social_Tarjeta` | El clip como tarjeta con esquinas redondeadas y sombra sobre un fondo de color (reels) | Tamaño, redondeo, color de fondo, sombra, aspecto |

---

# Lote 8: texto social, transiciones, cámaras y clima

## Títulos de texto (Titles › PRO Pack)

| Pieza | Para qué | Controles principales |
|---|---|---|
| `PRO_TTL_Texto_Maquina` | La frase aparece letra a letra, con cursor parpadeante (estilo máquina de escribir) | Texto, fuente (Courier New por defecto), tamaño, color, inicio del texto, cursor. **La duración de la entrada es lo que tarda en escribirse** (60 % del clip por defecto) |
| `PRO_TTL_Texto_Resaltado` | Palabra con un resaltador que se dibuja detrás de izquierda a derecha (subtítulos tipo CapCut) | Texto, fuente, colores del texto y del resaltado, ancho, alto, inclinación. *Ajusta el ancho al de tu texto a mano* |
| `PRO_TTL_Texto_Brillo` | Destello diagonal que recorre el texto cada cierto tiempo (logos, títulos "premium") | Texto, fuente, color, fotogramas entre destellos, intensidad y ancho del destello |
| `PRO_TTL_Texto_Neon` | Letrero de neón que se enciende parpadeando y falla de vez en cuando | Texto, fuente, color, brillo y radio del halo, fallos de parpadeo |

## Transiciones (Video Transitions › PRO Pack)

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_TR_ZoomRadial` | A se lanza hacia la cámara con desenfoque radial y B llega desde ella | Zoom, desenfoque radial |
| `PRO_TR_Giro` | La imagen gira y cambia de clip en mitad del giro | Giro en grados (negativo = al otro lado), zoom para tapar esquinas, desenfoque |
| `PRO_TR_Barras` | 8 barras verticales entran escalonadas, alternando arriba y abajo, y descubren el clip B | Escalonado, alternar, aspecto del timeline |
| `PRO_TR_Iris` | Círculo que crece desde un punto, con aro de color | Origen X/Y, grosor y color del aro, suavidad, tamaño final |

## Efectos (Effects › PRO Pack)

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_FX_Cam_REC` | Interfaz de videocámara: REC parpadeante, código de tiempo que corre, batería y esquinas | Color, opacidad, texto inferior, FPS, código inicial, batería, margen/largo/grosor de esquinas, aspecto |
| `PRO_FX_Cam_Seguridad` | Cámara de seguridad: casi sin color, tinte verdoso, ruido, líneas, nombre, fecha y reloj | Nombre, fecha, hora inicial, FPS, color, tinte, ruido, líneas, viñeta, color del texto |
| `PRO_FX_Cam_VisionNocturna` | Visión nocturna verde con brillo, grano y visor circular | Amplificación, color, brillo, grano, visor (tamaño y suavidad) |
| `PRO_FX_Cam_Termica` | Cámara térmica: frío (azul) → medio (magenta) → caliente (amarillo) | Tres colores, contraste, suavidad, mezcla |
| `PRO_FX_Retro_CRT` | Televisor de tubo: separación de color, líneas, parpadeo y pantalla redondeada | Separación, brillo, líneas, número de líneas, parpadeo, marco, redondeo, viñeta, aspecto |
| `PRO_FX_Social_PantallaDividida` | Pantalla dividida: pon cada clip en su pista con este efecto y elige su celda | Columnas, filas, columna y fila del clip, separación, redondeo, zoom, encuadre X/Y, aspecto |
| `PRO_FX_Din_KenBurns` | Zoom y paneo lentos para fotos y planos fijos; se adapta a la duración del clip | Zoom inicial/final, desplazamiento X/Y inicial/final, suavizado |
| `PRO_FX_Luz_Rayos` | Rayos de luz que salen de las luces altas desde un punto (ventanas, sol entre árboles) | Origen X/Y, largo, intensidad, umbral, color, refuerzo |
| `PRO_FX_Clima_Lluvia` | Lluvia en dos capas, inclinada por el viento, con la escena algo más oscura | Cantidad, brillo, velocidad, viento, oscurecer |
| `PRO_FX_Clima_Nieve` | Nieve en tres capas de profundidad con vaivén | Cantidad, brillo, velocidad, viento, desenfoque de copos cercanos |

---

# Lote 9: estilos de texto, horizontal ↔ vertical y looks

Todos los estilos tienen **Formato vertical (9:16)**, Posición, Escala y duraciones de entrada y salida. La fuente de cada uno y dónde descargarla está en [fuentes.md](fuentes.md).

## Estilos de texto (Titles › PRO Pack)

| Pieza | Fuente | Para qué | Controles propios |
|---|---|---|---|
| `PRO_TTL_Estilo_Viral` | Montserrat Black | Subtítulo de reels: dos líneas en mayúsculas, contorno negro grueso, palabra clave amarilla, entrada con rebote | Línea 1, palabra clave, colores, contorno (color y grosor), rebote |
| `PRO_TTL_Estilo_Gancho` | Anton + Montserrat | Gancho de los primeros segundos: titular amarillo con sombra dura que cae de golpe y tiembla | Titular, apoyo, sombra (color y desplazamiento), fuerza del golpe, temblor, inclinación |
| `PRO_TTL_Estilo_Trailer` | Bebas Neue + Montserrat Light | Título de trailer: aparece desenfocado y las letras se separan despacio durante todo el clip | Título, subtítulo, separación de letras |
| `PRO_TTL_Estilo_Elegante` | Segoe Script + Montserrat Light | Bodas y lifestyle: nombres caligráficos, fecha espaciada y línea fina | Nombres, fecha, fuentes, color |
| `PRO_TTL_Estilo_Minimal` | Poppins SemiBold + Light | Vlog y corporativo: sube, aparece y aprieta el espaciado | Título, subtítulo, fuentes, colores |
| `PRO_TTL_Estilo_Documental` | Roboto Condensed + Roboto | Video ensayo: título en caja negra y lugar o fecha en caja blanca, abajo a la izquierda | Textos, fuentes, colores de texto y de caja |
| `PRO_TTL_Estilo_Deportivo` | Teko | Rótulo deportivo: barra inclinada del color del equipo, entra rápido con desenfoque | Nombre, dato, color del equipo |
| `PRO_TTL_Estilo_Retro80` | Monoton + Montserrat | Synthwave: neón rosa con sombra cian, se enciende parpadeando | Título, subtítulo, sombra, halo |
| `PRO_TTL_Estilo_Gamer` | Press Start 2P | Pixel art: aparece a saltos y "PRESS START" parpadea | Título, texto que parpadea, fuentes, colores |
| `PRO_TTL_Estilo_Nota` | Ink Free | UGC: nota a mano con subrayado de rotulador y vaivén | Texto, color del subrayado, ancho, vaivén |

## Efectos y transición

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_FX_Din_Eco` | Estela de copias retrasadas detrás del movimiento (velocity edits, bailes) | Separación (fotogramas), intensidad, decaimiento, original transparente |
| `PRO_FX_Din_DesenfoqueMovimiento` | Desenfoque direccional, fijo o solo al inicio del clip (cortes de velocidad) | Intensidad, ángulo, solo al inicio, duración del pico |
| `PRO_FX_Social_Reencuadre` | Clip horizontal en timeline vertical (o al revés) con fondo desenfocado del mismo clip | Aspecto del clip y del timeline, desenfoque y brillo del fondo, zoom, escala, posición, redondeo |
| `PRO_FX_Social_ZonaSegura` | Guía de edición: zonas que tapa la interfaz de TikTok, Reels o Shorts, o marcos seguros 16:9. **Quítala antes de exportar** | Vertical, zonas superior, inferior y derecha, color, opacidad, aspecto |
| `PRO_FX_Look_Digicam` | Cámara digital de los 2000: saturada, con brillo, ruido fino y fecha naranja | Fecha, color, posición, saturación, brillo, ruido |
| `PRO_TR_Remolino` | Transición: la imagen se retuerce hasta el centro y se destuerce en el clip B | Giro, radio |

## Looks nuevos (página Color › LUTs › PRO_Pack)

| LUT | Para qué |
|---|---|
| `PRO_Look_CozyAmbar` | Estética cozy y flat-lay: cálido, ámbar, verdes apagados |
| `PRO_Look_DigicamY2K` | Cámara digital: contraste y saturación altos, sombras frías (combínalo con `Look_Digicam`) |
| `PRO_Look_LimpioLuminoso` | "Clean girl" o lifestyle: luminoso, poco contraste, piel rosada |

---

# Lote 10: generadores (Generators › PRO Pack)

Los que van "sobre negro" se usan en una pista superior con **Composite Mode = Screen** (o Add) en el Inspector, para que solo se sume la luz.

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_GEN_Aurora` | Degradado de malla: cuatro manchas de color que derivan y se mezclan. Fondo moderno para títulos, intros y reels | Color de fondo, Colores 1-4, velocidad, intensidad, suavidad, textura, saturación |
| `PRO_GEN_FugaLuz` | Fuga de luz orgánica sobre negro, para poner encima de cualquier plano (modo Screen) | Intensidad, cantidad de luz, velocidad, tres colores, suavidad |
| `PRO_GEN_EstaticaTV` | Estática de televisión con líneas y banda que rueda; entre cortes o como pantalla apagada | Contraste, brillo, tinte, líneas, banda, viñeta |
| `PRO_GEN_CuentaRegresiva` | Cola de película: números que bajan cada segundo, aros, cruz y línea que gira, con grano | Empieza en, FPS, colores, fuente, grano, parpadeo, viñeta |
| `PRO_GEN_Brasas` | Chispas que suben y titilan sobre negro (modo Screen): fuego, épica, trailers | Cantidad, brillo, velocidad, color, resplandor |
| `PRO_GEN_Synthwave` | Atardecer synthwave: cielo degradado, sol con franjas y rejilla en perspectiva que avanza. Combina con `Estilo_Retro80` | Formato vertical, velocidad, brillo y color de las líneas, color del suelo |

**Lo que Resolve ya trae** (Effects Library › Generators): Starfield, Paper, Polka Dots, Radial Lines, Soft Waves, Honeycomb y otros. No se duplicaron.

---

# Lote 11: dinámicos para videos virales

**Efectos al ritmo:** `PulsoRitmo`, `Estrobo`, `Clones` (y `ImpactoFrames` con "Repetir en cada golpe") usan **BPM**, **FPS** y **Desfase**. Pon el BPM de la canción y el FPS de la timeline. Mueve el desfase hasta que el primer golpe del efecto caiga en el primer golpe de la música. Aplícalos a un **Adjustment Clip** que cubra todo el tramo.

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_FX_Din_PulsoRitmo` | Zoom (y opcionalmente flash y sacudida) en cada golpe de la música: el clásico edit al ritmo | BPM, FPS, desfase, zoom, flash, sacudida, rapidez de la caída |
| `PRO_FX_Din_Estrobo` | En golpes alternos, la imagen pasa a blanco y negro duro o a negativo | BPM, FPS, desfase, negativo, intensidad, contraste |
| `PRO_FX_Din_ImpactoFrames` | Impact frames de anime: fotogramas en blanco y negro extremo que alternan con su negativo, con sacudida. Al inicio del clip o en cada golpe | Duración (fotogramas), repetir en cada golpe, sacudida, umbral, BPM |
| `PRO_FX_Din_Clones` | El clip repetido en mosaico (2×2, 3×3…), fijo o creciendo en cada golpe, con espejo opcional | Clones por lado, cambiar al ritmo, máximo, espejo, BPM |
| `PRO_TR_Puertas` | A se parte por la mitad y cada lado sale hacia fuera mientras B se acerca detrás | Zoom del clip B |
| `PRO_TR_Rebote` | A coge impulso y se encoge; B aparece de golpe con rebote | Fuerza del rebote, giro, color de fondo |
| `PRO_TR_RevelaLiquido` | Manchas orgánicas crecen y descubren B, con borde de color | Suavidad, borde, color, tamaño de las manchas |
| `PRO_TR_AntesDespues` | Antes y después: la línea se detiene a la mitad para comparar, con etiquetas. **Alarga la transición** (2-4 s) para que la pausa se note | Pausa, etiquetas y sus textos, color de la línea |
| `PRO_TTL_Social_Comentario` | Burbuja de "responder al comentario" con avatar, que entra con pop | Cabecera, comentario, fuente, colores, ancho, rebote, formato vertical |
| `PRO_TTL_Social_Ranking` | Número enorme (#1, #2…) en Anton para vídeos de top, con golpe de entrada y nombre debajo | Puesto, nombre, fuentes, colores, fuerza del golpe, formato vertical |

**Consejo para velocity edits:** combina el **Retime** de Resolve (curva de velocidad del clip) con `PulsoRitmo` o `ImpactoFrames` en el golpe, y con `Din_Eco` o `Din_DesenfoqueMovimiento` en el tramo rápido.

---

# Lote 12: comentario con foto y más transiciones

## `PRO_FX_Social_ComentarioFoto`: comentario con la foto del usuario
Es la misma burbuja que `PRO_TTL_Social_Comentario`, pero el avatar es una foto.
1. Arrastra la foto del usuario (captura o imagen de perfil) a una pista **por encima** del vídeo y dale la duración que quieras.
2. Aplícale el efecto `PRO_FX_Social_ComentarioFoto` (Effects › PRO Pack).
3. La foto desaparece y queda solo la burbuja, con el centro de la foto recortado en círculo como avatar.
4. Ajusta **Zoom de la foto** y **Encuadre X/Y** para centrar la cara. En una timeline vertical marca **Formato vertical (9:16)**: así el círculo y los textos quedan dentro de la caja.

Controles: los del comentario (cabecera, comentario, fuente, color, ancho, rebote, formato vertical, posición, escala) más zoom y encuadre de la foto.

## Transiciones

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_TR_DestelloLente` | Un núcleo de luz cruza la imagen con raya anamórfica y tapa el corte con un golpe de luz | Intensidad, altura del destello, colores del núcleo y de la raya |
| `PRO_TR_ZoomTraves` | Zoom a través de un punto de A (un ojo, una ventana, una pantalla) y salida desde un punto de B | Punto de A (X/Y), punto de B (X/Y), zoom, desenfoque |
| `PRO_TR_EstaticaTV` | Cambio de canal: ráfaga de estática con líneas y saltos | Estática, saltos, líneas |
| `PRO_TR_Apagon` | La luz de A parpadea hasta apagarse y B se enciende parpadeando | Velocidad del parpadeo |
| `PRO_TR_Corte` | Corte de espada: una línea blanca raja A en diagonal y las mitades se deslizan | Ángulo, distancia, color de la línea, aspecto |

---

# Lote 13: iconos animados (Titles › PRO Pack)

Los iconos están dibujados con formas de Fusion: no necesitan imágenes ni fuentes de iconos. Todos tienen **Formato vertical (9:16)**: márcalo en timelines verticales para que las formas no se deformen. También tienen Posición, Escala y duración de entrada y salida.

| Pieza | Para qué | Controles |
|---|---|---|
| `PRO_TTL_Icono_Like` | Corazón que aparece con rebote, suelta una explosión de puntos y late | Color, texto, rebote, latido |
| `PRO_TTL_Icono_Play` | Botón de reproducir estilo YouTube que pulsa, con texto debajo | Color del botón y del triángulo, texto, rebote |
| `PRO_TTL_Icono_Checklist` | Tres puntos que se marcan con un check verde que salta (pasos, tutoriales) | Puntos 1-3, fuente, color del check, rebote |
| `PRO_TTL_Icono_Ubicacion` | Pin que cae y rebota sobre su sombra, con el nombre del lugar | Lugar, fuente, color, rebote |
| `PRO_TTL_Icono_Flecha` | Flecha que señala y rebota sin parar | Ángulo, color, recorrido, rebote |
| `PRO_TTL_Icono_Estrellas` | Valoración de 0 a 5 estrellas que aparecen una a una | Estrellas encendidas, color, texto, rebote |
| `PRO_TTL_Icono_Redes` | Círculo con @ que salta y una pastilla que se abre con tu usuario | Usuario, símbolo, colores, ancho, rebote |
| `PRO_TTL_Icono_Cursor` | Cursor que llega al centro y hace clic con una onda | Colores, punto de partida X/Y |

Las estrellas usan el carácter ★ de la fuente Segoe UI Symbol, que viene con Windows.
