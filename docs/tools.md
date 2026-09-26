# Drawing Tools

Pixpop ships with nine tools, selectable from the tool picker or by cycling
with ++d++ (next) and ++a++ (previous). Hover any tool button to see its
tooltip.

![Line tool in action](assets/images/tools-line.svg)

## Pen

Freehand drawing. Click or drag to paint with the current brush size and pen
color. This is the default tool.

- **Brush size:** ++w++ / ++s++, sizes 1–5

## Fine pen

A precise single-pixel pen that works around the half-character limitation of
terminal drawing. Each terminal cell holds two stacked pixels, and the mouse
can only report the cell — so the fine pen lets *you* pick which pixel to
paint:

| Button | Pixel painted |
|---|---|
| Left-click | Top pixel |
| Right-click | Bottom pixel |
| Middle-click | Both pixels |

!!! note
    The fine pen always paints single pixels — brush size does not apply.

## Spray

Spray-paint effect: each click or drag scatters pixels at random within the
brush radius.

- **Brush size:** ++w++ / ++s++, sizes 1–5 (radius of the spray area)
- **Density:** adjustable via the spray density picker, 1–5
- Supports [normalized mode](#normalized-mode)

## Fill (paint bucket)

Flood-fills the contiguous region under the cursor with the pen color.

## Eraser

Erases pixels back to the transparent background. Behaves like the pen but
removes paint instead of adding it.

- **Brush size:** ++w++ / ++s++, sizes 1–5

## Line

Draws a straight line. Click to set the start, drag to see a live preview,
and release to commit.

- **Brush size:** sizes 1–5
- Supports [normalized mode](#normalized-mode)

## Rectangle

Draws a rectangle outline between the drag start and release points, with
live preview.

- **Brush size:** sizes 1–3 (outline thickness)

## Circle

Draws a circle. The drag defines a bounding box; the circle is anchored
inside it, with live preview.

- **Brush size:** sizes 1–3
- Supports [normalized mode](#normalized-mode)

## Ellipse

Draws an ellipse inscribed in the drag bounding box, with live preview.

- **Brush size:** sizes 1–3
- Supports [normalized mode](#normalized-mode)

## Shape tool tips

All shape tools (line, rectangle, circle, ellipse) share the same workflow:

1. **Mouse down** — anchor the shape
2. **Drag** — live preview of the outline
3. **Release** — commit the shape in the pen color

Committing with the **right button** draws the shape in the background color
instead, effectively cutting the shape out of existing paint.

## Normalized mode

Because two pixels share one terminal cell, diagonal strokes can look
"steppy". Normalized mode snaps painted pixels to even rows so that strokes
made by the **line**, **circle**, **ellipse**, and **spray** tools form
whole characters — producing smoother, more uniform ANSI art.

Toggle it with the **Normalized** picker in the side panel. It only affects
tools that support it.
