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
