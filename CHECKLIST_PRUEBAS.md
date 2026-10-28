# Checklist de pruebas en Resolve (≈10 min)

Nada de esto se ha probado en Resolve. Cada casilla confirma un **patrón** que después se repetirá en unas 60 piezas, así que es la prueba más rentable del proyecto.

**Cómo reportar:** para cada número, dime ✅ o ❌. Si algo falla, añade el texto del error o una captura. Si una plantilla no aparece, mira la consola de Fusion (página Fusion › Workspace › Console).

## 0. Instalación
- [ ] 0.1 `install.ps1 -DryRun` muestra 6 archivos nuevos y 0 backups.
- [ ] 0.2 `install.ps1`, ejecutado como administrador, termina con "Listo".
- [ ] 0.3 Tras reiniciar Resolve, cada categoría (Video Transitions, Titles, Generators, Effects) muestra un grupo **PRO Pack**.

## 1. Transición `PRO_TR_BlurDissolve_Flash` (prueba el patrón de 2 entradas y Anim Curves)
- [ ] 1.1 Aparece en Video Transitions › Fusion Transitions y se puede arrastrar a un corte.
- [ ] 1.2 Sale del clip A y termina en el clip B (no al revés).
- [ ] 1.3 El desenfoque llega al máximo a mitad de la transición. Cambia la duración (por ejemplo, de 1 s a 2 s) y comprueba que la animación se estira.
- [ ] 1.4 En el Inspector se ven Desenfoque, Flash y Color del flash. Con Flash = 0.5 aparece un destello en el centro.
- [ ] 1.5 Funciona en una timeline 4K y en una vertical 1080×1920.

## 2. Título `PRO_TTL_Corp_LowerThird` (prueba Text+, colores y expresiones)
- [ ] 2.1 Se ven el nombre y el cargo alineados a la izquierda, con la barra a su izquierda. *Si el texto está centrado sobre la barra, falla `HorizontalLeftCenterRight`.*
- [ ] 2.2 Animación: entra, se queda quieto y sale. *Si nunca aparece, falla la expresión de envolvente (Anim Curves o `min`/`max`).*
- [ ] 2.3 Las tildes se ven bien en las etiquetas del Inspector ("Posición", "Duración").
- [ ] 2.4 Cambiar Fuente, Colores, Posición y Escala funciona.
- [ ] 2.5 La barra tiene una proporción razonable (fina y algo más alta que el bloque de texto). *Si no, anota cómo se ve: la unidad de Width/Height de la máscara es una incógnita.*

## 3. Efecto `PRO_FX_Cine_GranoHalation` (prueba el patrón de 1 entrada)
- [ ] 3.1 Aplicado a un clip con luces fuertes (ventana, farolas), se ve un halo rojizo alrededor de las altas luces.
- [ ] 3.2 Hay grano visible, distinto en cada fotograma.
- [ ] 3.3 "Grano (finura)" a 80: ¿el grano es más fino o más grueso? Anótalo.
- [ ] 3.4 Funciona sobre un Adjustment Clip.
- [ ] 3.5 En una timeline 4K, el halo y el grano cubren toda la imagen (no solo un rectángulo centrado).

## 4. Generador `PRO_GEN_Fondo_Luz`
- [ ] 4.1 Muestra un fondo oscuro con una luz difusa que se mueve lentamente.
- [ ] 4.2 Con Movimiento = 0 queda estático; con 2, da dos vueltas en la duración del clip.

## 5. Color
- [ ] 5.1 Aparece la carpeta PRO_Pack en el LUT Browser (página Color).
- [ ] 5.2 `PRO_Look_TealOrange` sobre un plano Rec.709 con piel: la piel queda cálida y las sombras tiran a cian, sin colores rotos.
- [ ] 5.3 El DCTL `PRO_TealOrange` aparece en ResolveFX DCTL, con 4 deslizadores.
- [ ] 5.4 Con los valores por defecto, el DCTL y el `.cube` se ven iguales (compáralos con el wipe de la Gallery).

## 6. Desinstalación
- [ ] 6.1 `uninstall.ps1`, como administrador, borra 6 archivos y las plantillas desaparecen al reiniciar Resolve.

---

### Incógnitas técnicas que cubre esta checklist
| Incógnita | Casillas |
|---|---|
| El modificador `LUTLookup` (Anim Curves) sin parámetros da un progreso 0→1 en títulos, efectos y generadores, no solo en transiciones | 1.3, 2.2, 4.2 |
| Las expresiones simples admiten `min`, `max`, `sin`, `cos` y `Point()` | 2.2, 4.1 |
| `Background` y `FastNoise` con `UseFrameFormatSettings` toman la resolución de la timeline | 1.5, 3.5 |
| Unidades de Width/Height en las máscaras | 2.5 |
| UTF-8 en los nombres del Inspector | 2.3 |
| Sentido del parámetro de escala de FastNoise | 3.3 |

## 7. Lote 2: dinámico y cine
- [ ] 7.1 Aparecen 7 efectos nuevos en Effects › PRO Pack y 3 transiciones nuevas en Video Transitions › PRO Pack.
- [ ] 7.2 `PunchIn`: el zoom entra al principio y se queda. `Shake` se mueve sin dejar ver bordes negros.
- [ ] 7.3 `RGBSplit`: se ven franjas roja y azul en los bordes. Con Pulso = 1, la separación late.
- [ ] 7.4 `FlashBeat`: hay un destello al inicio del clip que se apaga.
- [ ] 7.5 `Letterbox` sobre un Adjustment Clip: las barras entran y la imagen queda en 2.39.
- [ ] 7.6 `Vineta` y `Difusion` se ven bien con los valores por defecto.
- [ ] 7.7 `WhipPan`: el clip B entra pegado al A, sin franja negra en medio. Prueba Dirección -1 y Barrido vertical.
- [ ] 7.8 `ZoomPunch` y `LightLeak` funcionan con duraciones de 10 y 30 fotogramas.
- [ ] 7.9 Los LUT `FrioThriller` y `FilmSuave` aparecen en PRO_Pack y no rompen la piel.

Incógnitas nuevas: el uso de `time` en expresiones (Shake, RGBSplit), el control `LockXY` del Blur (WhipPan) y el control de tipo casilla `CheckboxControl` (WhipPan).

## 8. Lote 3: lentes
- [ ] 8.1 Aparecen 5 efectos `PRO_FX_Lente_*` en Effects › PRO Pack.
- [ ] 8.2 `Anamorfico` en un plano nocturno con luces: se ven rayas horizontales azules que salen de las luces.
- [ ] 8.3 `Vintage` y `Lomo`: las esquinas se ven más blandas que el centro, sin bordes negros ni franjas en los extremos de la imagen.
- [ ] 8.4 `AberracionRadial` con Intensidad 5: hay franjas de color en los bordes y el centro queda limpio.
- [ ] 8.5 `TiltShift`: la franja enfocada se mueve con "Posición" y gira con "Ángulo". *Anota si la franja sale mucho más ancha o estrecha de lo esperado (unidades de la máscara).*

## 9. Lote 4: estilo plugins de pago
- [ ] 9.1 `Film_Completo`: con Formato 8, el grano y el vaivén son claramente mayores que con 65.
- [ ] 9.2 `Film_Proyector`: hay motas oscuras que cambian en cada fotograma y, de vez en cuando, una raya vertical.
- [ ] 9.3 `Lente_Flare`: al mover "Posición del destello", los fantasmas se desplazan en sentido opuesto respecto al centro.
- [ ] 9.4 `Retro_VHS`: el color se corre hacia los lados. *Si el modo de fusión "Color" no existe, solo se verá desenfoque horizontal: anótalo.*
- [ ] 9.5 `TR_Glitch` y `TR_FilmBurn` funcionan con duraciones de 10 y 30 fotogramas.
- [ ] 9.6 Los LUT `PeliculaPrint` y `BN_Contraste` aparecen en PRO_Pack.

Incógnitas nuevas: acceso a `.X` y `.Y` de un punto en expresiones (Lente_Flare, FilmBurn) y los modos de fusión "Color" (VHS) y "Difference" (polvo).

## 10. Lote 5: transiciones de cinta
- [ ] 10.1 Aparecen 4 transiciones nuevas en Video Transitions › PRO Pack (el registro debe mostrar 400 plantillas).
- [ ] 10.2 `SaltoCinta`: el clip A sube, se ve una franja negra y entra el B, sin huecos raros.
- [ ] 10.3 `CintaPelicula`: al alejarse la imagen se ven perforaciones a ambos lados, que avanzan con la imagen. *Si solo aparece UNA perforación por lado, el encadenado de máscaras no funciona: avísame.* Anota también si su forma está achatada o estirada.
- [ ] 10.4 `QuemaOrganica`: las manchas tienen forma irregular, bordes naranjas y crecen hasta el centro de la transición.
- [ ] 10.5 `FlashFotogramas`: la imagen alterna entre los dos clips con destellos y termina limpia en el B.
- [ ] 10.6 En las 4, el primer y el último fotograma de la transición se ven limpios, sin polvo ni rayas.

## 11. Lote 6: reels
- [ ] 11.1 `SombraLarga` sobre un PNG recortado: la sombra sale detrás del objeto, en el ángulo indicado, y se desvanece.
- [ ] 11.2 `Halftone`: se ven puntos en una rejilla regular, más grandes en las zonas oscuras. *Si la imagen sale toda blanca o toda negra, falla el modo aditivo del Merge (SubtractiveAdditive): avísame.*
- [ ] 11.3 `Anim_Flow`: el clip entra desde la izquierda con un pequeño rebote. Con Zoom -1 hace "pop". Con "Modo salida" sale al final.
- [ ] 11.4 `TR_Empuje`: la escena se empuja sin huecos y hay un destello en el centro.
- [ ] 11.5 `AnilloGiratorio`: se ven 24 guiones formando un círculo, no un óvalo, en una timeline vertical, y giran. *Si solo aparece un guion, falla el encadenado de máscaras (igual que en la 10.3).*
- [ ] 11.6 `Cuadricula`: hay líneas finas, celdas cuadradas y bordes desvanecidos.
- [ ] 11.7 `TextoPop`: el texto entra con rebote y sale al final.

## 12. Lote 7: gráficos, generadores y efectos
- [ ] 12.1 `Contador`: el número sube de 0 a 1000 y se detiene. *Si se queda en "0", el texto por expresión (`string.format`) no funciona: avísame.*
- [ ] 12.2 `Titulo_Apertura`: las letras empiezan separadas y se juntan. *Si no cambian, `CharacterSpacing` tiene otro nombre.*
- [ ] 12.3 `Barra_Progreso`: el relleno crece de izquierda a derecha durante todo el clip.
- [ ] 12.4 `Callout_Flecha`: al mover "Punto señalado" en el visor, la línea y el texto lo siguen.
- [ ] 12.5 `EndScreen`, `Suscribete`, `Cita`, `Separador` y `LineaTiempo`: los elementos aparecen escalonados y salen al final.
- [ ] 12.6 `Degradado_Animado` y `Duotono` muestran los dos colores mezclados. *Si salen saturados o blancos, falla el modo aditivo (igual que en la 11.2).*
- [ ] 12.7 `Bokeh`: hay luces suaves que se mueven despacio. `Polvo_Flotante`: motas pequeñas que derivan.
- [ ] 12.8 `Glow_Neon` sobre un plano con neones: halo de color alrededor de las luces.
- [ ] 12.9 `Social_Tarjeta` en una timeline vertical: tarjeta redondeada con sombra, sin bordes cortados.

## 13. Lote 8: texto social, transiciones, cámaras y clima
- [ ] 13.1 Aparecen 18 piezas nuevas (el registro debe mostrar 440 plantillas).
- [ ] 13.2 `Texto_Maquina`: la frase se escribe letra a letra desde el punto de inicio hacia la derecha y el cursor parpadea. *Si no sale nada, falla leer el texto de otro nodo (`Fuente.StyledText.Value`) o el texto por expresión (como en 12.1). Si una letra con tilde se ve rara durante un fotograma, es normal (Lua cuenta bytes, no letras).*
- [ ] 13.3 `Texto_Resaltado`: la banda crece de izquierda a derecha detrás del texto, sin taparlo.
- [ ] 13.4 `Texto_Brillo`: una franja brillante cruza el texto cada 60 fotogramas y solo se ve sobre las letras.
- [ ] 13.5 `Texto_Neon`: parpadea al entrar y después falla de vez en cuando; tiene halo de color.
- [ ] 13.6 `TR_ZoomRadial` y `TR_Giro`: sin huecos negros en los bordes. En `Giro`, el clip B termina derecho.
- [ ] 13.7 `TR_Barras`: cada barra cubre toda la altura y entran una tras otra. *Si las barras son más cortas que la pantalla o no salen del todo, el alto de las máscaras no está en las unidades que supuse (igual que en 12.9): avísame.*
- [ ] 13.8 `TR_Iris`: es un círculo, no un óvalo, y al final no quedan esquinas del clip A.
- [ ] 13.9 `Cam_REC`: el punto rojo parpadea cada segundo, el código de tiempo avanza y las 4 esquinas tienen forma de L. *Si el código se queda en 00:00:00:00, falla `string.format` (como en 12.1).*
- [ ] 13.10 `Cam_Seguridad`: el reloj avanza desde 14:30:00 y hay líneas horizontales finas.
- [ ] 13.11 `Cam_Termica`: las zonas oscuras salen azules, las medias magenta y las claras amarillas. *Si sale blanco o saturado, falla el modo aditivo (como en 11.2).*
- [ ] 13.12 `Cam_VisionNocturna` y `Retro_CRT` se ven bien en una timeline 4K.
- [ ] 13.13 `PantallaDividida`: dos clips en dos pistas, uno con Fila 1 y otro con Fila 2, llenan la pantalla vertical sin huecos (salvo la separación).
- [ ] 13.14 `KenBurns`: la imagen se acerca y se desplaza durante todo el clip sin mostrar bordes.
- [ ] 13.15 `Luz_Rayos`: los rayos salen del punto de origen y se alargan alejándose de él.
- [ ] 13.16 `Clima_Lluvia` y `Clima_Nieve`: las gotas y los copos **caen hacia abajo**. *Si suben, el sentido del centro de FastNoise está al revés: avísame y lo invierto en el script.*

## 14. Lote 9: estilos de texto, horizontal ↔ vertical y looks
Antes de probar, instala las fuentes de [docs/fuentes.md](docs/fuentes.md) (o comprueba que ya las tienes).
- [ ] 14.1 Aparecen 16 plantillas nuevas (el registro debe mostrar 456) y 3 LUT nuevas en PRO_Pack.
- [ ] 14.2 `Estilo_Viral`: el texto tiene un contorno negro grueso y una sombra suave. *Si no hay contorno ni sombra, fallan los elementos de sombreado de Text+ (Enabled2, Enabled8): avísame.*
- [ ] 14.3 `Estilo_Gancho`: el titular tiene una sombra dura desplazada, cae desde grande y tiembla un momento al aterrizar.
- [ ] 14.4 `Estilo_Documental`: cada texto tiene su caja de color detrás. *Si no hay caja, falla el elemento 6 (ElementShape = 2, Level = 1).*
- [ ] 14.5 En los 10 estilos, el Inspector muestra la fuente correcta (no Arial). Si sale otra, esa fuente no está instalada o tiene otro nombre: dime cuál.
- [ ] 14.6 Marca **Formato vertical (9:16)** en una timeline vertical: el bloque se recoloca, no se corta y queda fuera de las zonas de `Social_ZonaSegura`.
- [ ] 14.7 `Estilo_Trailer`: las letras se separan despacio durante todo el clip. `Estilo_Gamer`: aparece a saltos y "PRESS START" parpadea.
- [ ] 14.8 `Din_Eco` sobre un plano con movimiento: se ven copias del sujeto detrás. *Si no se ven, `TimeSpeed` no recibe fotogramas anteriores en la página Edit: avísame.*
- [ ] 14.9 `Din_DesenfoqueMovimiento`: el desenfoque va en la dirección del ángulo.
- [ ] 14.10 `Social_Reencuadre`: un clip 16:9 en una timeline 9:16 queda centrado, con fondo desenfocado y sin franjas negras. *Si el clip sale recortado o con franjas, dime cómo ajusta Resolve el clip (Image scaling) en tu proyecto.*
- [ ] 14.11 `Social_ZonaSegura`: en vertical, las bandas rojas están arriba, abajo y a la derecha. Desmarcando "Vertical" se ven dos marcos verdes en 16:9.
- [ ] 14.12 `Look_Digicam`: la fecha naranja aparece abajo a la derecha. `TR_Remolino`: la imagen se retuerce y termina limpia en el clip B.

## 15. Lote 10: generadores y cambios en CintaPelicula
- [ ] 15.1 `TR_CintaPelicula`: hay mucho menos polvo, rayas y parpadeo que antes, y una fuga de luz naranja cruza la imagen a mitad de la transición.
- [ ] 15.2 Aparecen 6 generadores nuevos (el registro debe mostrar 462 plantillas).
- [ ] 15.3 `GEN_Aurora`: manchas de color suaves que se mueven despacio, sin bordes visibles.
- [ ] 15.4 `GEN_FugaLuz` y `GEN_Brasas` encima de un clip con modo Screen: solo se suma la luz, el negro desaparece. Las brasas **suben**. *Si bajan, avísame (sentido del centro de FastNoise, igual que en 13.16).*
- [ ] 15.5 `GEN_EstaticaTV`: el ruido cambia en cada fotograma y una banda clara recorre la imagen de arriba abajo.
- [ ] 15.6 `GEN_CuentaRegresiva`: el número baja de 5 a 1, uno por segundo, y la línea da una vuelta cada segundo. *Si el número no cambia, falla el texto por expresión (como en 12.1).*
- [ ] 15.7 `GEN_Synthwave`: las líneas verticales de la rejilla convergen en el horizonte, debajo del sol. Marca "Formato vertical" en una timeline 9:16 y comprueba que siguen convergiendo. *Si forman una X o se abren hacia arriba, el sentido del ángulo de las máscaras está al revés: avísame.*

## 16. Lote 11: dinámicos para videos virales
- [ ] 16.1 Aparecen 10 piezas nuevas (el registro debe mostrar 472 plantillas).
- [ ] 16.2 `Din_PulsoRitmo` con BPM 120 y FPS 30: hay un golpe de zoom cada 15 fotogramas que cae enseguida. Con el desfase, el golpe se mueve.
- [ ] 16.3 `Din_Estrobo`: un golpe en color, el siguiente en blanco y negro (o negativo si se marca).
- [ ] 16.4 `Din_ImpactoFrames`: los 6 primeros fotogramas del clip son blanco y negro extremo, alternando con el negativo cada 2 fotogramas, y después vuelve al original.
- [ ] 16.5 `Din_Clones` con 2: el clip aparece 4 veces (2×2). *Si sale pequeño en el centro con negro alrededor, el modo de bordes "Wrap" (Edges = 1) no se aplica: avísame. Si "Espejo" no cambia nada, el valor 3 no es Mirror.*
- [ ] 16.6 `TR_Puertas`: A se abre por el centro sin huecos, y B está detrás.
- [ ] 16.7 `TR_Rebote`: A se agranda un poco, se encoge hasta desaparecer y B aparece con rebote.
- [ ] 16.8 `TR_RevelaLiquido`: B aparece por manchas que crecen. *Si sale saturado o blanco, falla el modo aditivo (como en 11.2).*
- [ ] 16.9 `TR_AntesDespues` con 3 s de duración: la línea llega al centro, se detiene, luego termina. Las etiquetas ANTES y DESPUÉS tienen caja negra.
- [ ] 16.10 `Social_Comentario`: la burbuja blanca entra con pop y el texto queda dentro. Si el comentario es largo, sube el "Ancho de la burbuja".
- [ ] 16.11 `Social_Ranking`: "#1" cae de grande con contorno y sombra, y el nombre aparece debajo.

## 17. Lote 12: comentario con foto y transiciones
- [ ] 17.1 `Social_ComentarioFoto` sobre una foto en V2: solo se ve la burbuja, con la foto recortada en círculo. Con Zoom de la foto = 1 el círculo queda lleno. *Si la foto sale pequeña o desplazada, revisa el Aspecto; si aun así falla, dime cómo ajusta Resolve la imagen al timeline.*
- [ ] 17.2 `TR_DestelloLente`: la luz cruza de izquierda a derecha y el corte queda tapado por el destello.
- [ ] 17.3 `TR_ZoomTraves`: con Punto de A en una cara, el zoom entra justo en ese punto y no se va hacia el centro.
- [ ] 17.4 `TR_EstaticaTV` y `TR_Apagon` funcionan con duraciones de 10 y 30 fotogramas.
- [ ] 17.5 `TR_Corte`: la línea aparece en diagonal y las mitades se separan **a lo largo** de la línea, sin huecos donde no toca. *Si el corte va en otra dirección que las mitades, el sentido del ángulo de las máscaras está al revés (como en 15.7).*

## 18. Lote 13: iconos animados y comentario corregido
- [ ] 18.1 `Social_Comentario` y `Social_ComentarioFoto` (con **Formato vertical** marcado si la timeline es 9:16): el avatar queda dentro de la caja blanca con margen, y los dos textos quedan a su derecha, centrados en vertical.
- [ ] 18.2 El avatar es un círculo, no un cuadrado redondeado. *Si sale cuadrado, "CornerRadius = 1" no redondea del todo: avísame.*
- [ ] 18.3 Aparecen 8 títulos `Icono_*` (el registro debe mostrar 488 plantillas).
- [ ] 18.4 `Icono_Like`: el corazón tiene forma de corazón (dos círculos arriba y punta abajo), con puntos que salen hacia fuera.
- [ ] 18.5 `Icono_Play` y `Icono_Ubicacion`: el triángulo aparece en su sitio. *Si no se ve, falla `TriangleMask` (Point1-3).*
- [ ] 18.6 `Icono_Checklist`: los checks salen a la izquierda de cada texto, uno tras otro.
- [ ] 18.7 `Icono_Flecha` con Ángulo 90: la flecha apunta a un lado y rebota en esa dirección.
- [ ] 18.8 `Icono_Estrellas` con 4: cuatro estrellas doradas y una gris.
- [ ] 18.9 `Icono_Redes` y `Icono_Cursor`: la pastilla se abre hacia la derecha; el cursor llega y hace clic con una onda.

## 19. Corrección de proporciones (D24)
- [ ] 19.1 En 16:9 y en 9:16 (con **Formato vertical** marcado): el avatar del comentario y los círculos de los iconos son redondos, el corazón tiene forma de corazón y el botón de play es un rectángulo redondeado, no una franja.
- [ ] 19.2 `EndScreen`: los dos marcos de vídeo tienen proporción 16:9. `Suscribete`: el botón es una pastilla, no una línea.
- [ ] 19.3 `Social_Tarjeta`, `Retro_CRT` y `TR_Barras` cubren el alto correcto sin necesitar el control de aspecto (ya no existe en ellas).
- [ ] 19.4 `Social_ZonaSegura` en 9:16: la banda inferior ocupa el 22 % del alto. `Social_Reencuadre`: el clip 16:9 en 9:16 se ve entero, sin recortar arriba ni abajo.
- [ ] 19.5 `TR_Corte`: las dos mitades se separan justo por la línea blanca.

## 20. Revisión horizontal / vertical (D25)
Prueba cada título en una timeline 1920×1080 y en otra 1080×1920. En la vertical, marca **Formato vertical (9:16)**.
- [ ] 20.1 En vertical, el título se ve igual que en horizontal (mismas proporciones entre texto, cajas e iconos) y no se sale por los lados.
- [ ] 20.2 `Estilo_Deportivo`: el nombre queda dentro de la barra y el dato se lee debajo, en blanco.
- [ ] 20.3 `Estilo_Documental` y `Estilo_Deportivo` en vertical quedan a la izquierda, por encima de la zona inferior de `Social_ZonaSegura`.
- [ ] 20.4 `Barra_Progreso` en vertical queda abajo del todo; `Suscribete`, por encima de la zona inferior.
- [ ] 20.5 `Cam_REC` (con Aspecto 0.5625), `Cam_Seguridad`, `Look_Digicam`, `GEN_CuentaRegresiva`, `TR_AntesDespues` y `Social_TextoPop` en vertical: el texto tiene un tamaño razonable y no tapa el centro.
- [ ] 20.6 Cambiar "Tamaño" en el Inspector de cualquier estilo sigue funcionando en los dos formatos.
