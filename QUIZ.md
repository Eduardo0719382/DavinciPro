# Quiz: 5 preguntas sobre el Resolve Pro Pack

1. **¿En qué carpeta instala el paquete un archivo `PRO_TTL_….setting` y por qué no necesita administrador, mientras que `PRO_Look_TealOrange.cube` sí lo necesita?**

2. **Aplicas `PRO_Look_TealOrange.cube` directamente sobre un clip en S-Log3 y se ve lavado y raro. ¿Qué te falta y en qué orden van los nodos?**

3. **Cambias la duración de `PRO_TR_BlurDissolve_Flash` de 12 a 48 fotogramas. ¿Qué pasa con la animación y qué mecanismo de Fusion lo hace posible?**

4. **¿Cuál de las 6 piezas del piloto no funcionaría en DaVinci Resolve gratuito, y qué alternativa del paquete usarías en su lugar?**

5. **Editaste a mano `PRO_GEN_Fondo_Luz.setting` después de instalarlo y luego ejecutas `uninstall.ps1`. ¿Qué hace con ese archivo y cómo lo borrarías si quisieras?**

<details><summary>Respuestas</summary>

1. En `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit\Titles`, que es una carpeta de tu usuario. El `.cube` va a `%ProgramData%\…\LUT\PRO_Pack`, una carpeta del sistema que solo puede escribir un administrador.
2. Falta convertir el material a Rec.709. Nodo 1: Color Space Transform (S-Gamut3/S-Log3 → Rec.709/Gamma 2.4). Nodo 2: el LUT.
3. Se estira y dura 48 fotogramas, con el desenfoque al máximo en la mitad. Lo permite el modificador **Anim Curves** (`LUTLookup`): da un progreso 0→1 relativo a la duración, no a fotogramas fijos.
4. `PRO_TealOrange.dctl`, porque el plugin DCTL es de Studio. En su lugar, `PRO_Look_TealOrange.cube`, regulando la intensidad con Key Output Gain.
5. Lo conserva y avisa, porque su hash ya no coincide con el del manifiesto. Para borrarlo: `uninstall.ps1 -Force`.
</details>
