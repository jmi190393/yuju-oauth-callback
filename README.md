# Combina — asesor de imagen para daltónicos

App web para combinar ropa cuando no distingues bien los colores. Subes fotos de
tus prendas, la app detecta el color y le pone nombre, y te dice qué combina con qué.

## Qué hace

- **Agregar prenda:** tomas o subes una foto; se detecta el color dominante y se
  nombra. Puedes corregir el color a mano antes de guardar.
- **Mi ropero:** las prendas se guardan en tu dispositivo (`localStorage`). Tus
  fotos **no se suben a ningún servidor**.
- **Elegir 1 prenda → qué le queda:** al seleccionar una sola prenda, la app
  muestra automáticamente con qué del ropero queda y se ve bien, ordenado de mejor
  a peor.
- **Evaluar conjunto:** seleccionas 2 o más prendas y te dice si el conjunto se ve
  bien, regular o mejor no, con una nota por cada par.

## Pensado para daltonismo rojo-verde

El veredicto **no depende del color**: se distingue por ícono + texto + textura del
borde.

| Veredicto      | Ícono | Forma            | Borde              |
|----------------|-------|------------------|--------------------|
| Se ve bien     | ✓     | cuadro redondeado| línea sólida       |
| Con cuidado    | !     | círculo          | línea a rayas      |
| Mejor evítalo  | ✕     | cuadro recto     | punteado + rayado  |

Cada prenda siempre muestra el **nombre del color por escrito**, que es lo que no
se puede percibir a simple vista.

- **Si no reconozco bien el color:** cuando la foto es ambigua (estampado, poca
  luz, fondo con color) te aviso y te pido otra foto, en vez de arriesgar un
  color equivocado.
- **Asesor con IA (opcional):** con tu propia clave de API de Anthropic, la IA
  analiza las fotos y da consejo de estilo más rico (color, formalidad, ocasión,
  estampados). Toca **🧠 IA** para pegar tu clave (se guarda solo en el
  dispositivo) y elegir el modelo.

## Cómo usarla

Es un solo archivo, sin dependencias ni build. Abre `index.html` en el navegador,
o publícalo con GitHub Pages y ábrelo desde el teléfono.

### Sobre el modo IA

El análisis con IA hace una llamada a la API de Anthropic desde el navegador, así
que **solo funciona cuando la app corre en una página real** (GitHub Pages o el
archivo abierto localmente), no dentro de una vista previa que bloquee la red.
Necesita una clave de API (de `console.anthropic.com`), tiene un pequeño costo por
uso y requiere conexión a internet. Todo lo demás (detección y nombres de color,
armado de conjunto) funciona sin IA, sin conexión y sin costo.

## Cómo funciona por dentro

- El color dominante se calcula en un `<canvas>`: se reduce la imagen, se muestrea
  la región central (donde suele estar la prenda) y se agrupan los píxeles,
  penalizando casi-blancos y casi-negros (fondo/sombra).
- El nombre del color sale de convertir RGB a HSL y clasificar por matiz, con casos
  especiales para neutros (negro, blanco, gris, beige, café, azul marino).
- La armonía entre dos prendas se calcula por la diferencia de matiz en la rueda de
  color (análogos, complementarios, triádicos) y trata los neutros como comodines.
