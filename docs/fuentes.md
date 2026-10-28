# Fuentes de los estilos de texto

Los 10 estilos `PRO_TTL_Estilo_*` usan cada uno la fuente que mejor le va. Las fuentes no vienen con el paquete. **Si una fuente no está instalada, Resolve la cambia por otra sin avisar**, así que en una PC nueva instálalas primero. Todas son gratuitas (Google Fonts, licencia OFL) o vienen con Windows.

| Estilo | Fuente principal | Fuente secundaria | Por qué esta fuente | Descarga |
|---|---|---|---|---|
| `Estilo_Viral` | Montserrat Black | (la misma) | Muy gruesa y geométrica: con contorno se lee incluso en pantallas pequeñas. Es la típica de los subtítulos de reels | [Montserrat](https://fonts.google.com/specimen/Montserrat) |
| `Estilo_Gancho` | Anton | Montserrat ExtraBold | Condensada y pesada: cabe mucho texto en grande, como en las miniaturas de YouTube | [Anton](https://fonts.google.com/specimen/Anton) |
| `Estilo_Trailer` | Bebas Neue | Montserrat Light | Solo mayúsculas, alta y estrecha: es el aspecto de los carteles y trailers | [Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue) |
| `Estilo_Elegante` | Segoe Script | Montserrat Light | Caligráfica para nombres; la secundaria fina y espaciada equilibra | Segoe Script viene con Windows |
| `Estilo_Minimal` | Poppins SemiBold | Poppins Light | Redonda y moderna; una sola familia en dos pesos queda limpia | [Poppins](https://fonts.google.com/specimen/Poppins) |
| `Estilo_Documental` | Roboto Condensed Bold | Roboto Regular | Neutra y periodística; la condensada cabe en cajas estrechas | [Roboto Condensed](https://fonts.google.com/specimen/Roboto+Condensed), [Roboto](https://fonts.google.com/specimen/Roboto) |
| `Estilo_Deportivo` | Teko SemiBold | Teko Regular | Muy condensada y cuadrada, como los rótulos de las retransmisiones deportivas | [Teko](https://fonts.google.com/specimen/Teko) |
| `Estilo_Retro80` | Monoton | Montserrat Bold | Letras de tubos de neón paralelos: synthwave al instante | [Monoton](https://fonts.google.com/specimen/Monoton) |
| `Estilo_Gamer` | Press Start 2P | (la misma) | Píxel de consola de 8 bits | [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) |
| `Estilo_Nota` | Ink Free | — | Parece escrita con rotulador: cercana, para UGC y vlogs | Ink Free viene con Windows |

Otras piezas: `Texto_Maquina` usa Courier New y `Look_Digicam` usa OCR A Extended (Windows / Office). El resto usa Arial.

## Instalar una fuente

1. Descarga la familia desde el enlace (botón "Get font", luego "Download all").
2. Descomprime el zip, selecciona los `.ttf` (o la carpeta `static`), haz clic derecho y elige **Instalar para todos los usuarios**.
3. Reinicia Resolve.

Si cambias la fuente en el Inspector, revisa también el **Tamaño**: cada fuente ocupa un ancho distinto.

## Horizontal (16:9) y vertical (9:16)

- **Todos los títulos** (estilos, iconos, comentario, gráficos animados) tienen la casilla **Formato vertical (9:16)**. Márcala en timelines verticales. El título se ve igual que en 16:9, a un tamaño adecuado para el ancho, y queda fuera de las zonas que tapan los botones de TikTok, Reels o Shorts. Sin marcarla, en vertical el texto sale unas 3 veces más grande que sus formas.
- Usa `PRO_FX_Social_ZonaSegura` en un clip de ajuste mientras editas, para ver qué zonas tapa la interfaz de cada red. **Quítalo antes de exportar.**
- Para usar un clip horizontal en una timeline vertical sin barras negras, aplica `PRO_FX_Social_Reencuadre`: rellena el fondo con el mismo clip ampliado y desenfocado. También sirve al revés.
