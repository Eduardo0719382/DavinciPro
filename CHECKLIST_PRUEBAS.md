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
