import sys
from typing import List, Tuple
from svgelements import SVG, Path, PathSegment, Line, Close, Point, Rect, Circle, Ellipse, SVGElement, Group
from tkinter import Tk, Canvas


def coords(*args: Point | Tuple[float, float]):
    return tuple(map(lambda x: (x[0], x[1]), args))


def rect_coords(rect: Rect):
    if rect.x and rect.y:
        return rect.x, rect.y, rect.x + rect.width, rect.y + rect.height
    return None


def oval_coords(oval: Circle | Ellipse):
    if oval.cx and oval.cy and oval.rx and oval.ry:
        return (
            (oval.cx - oval.rx, oval.cy - oval.ry),
            (oval.cx + oval.rx, oval.cy + oval.ry)
        )
    return None


def is_path_closed(path: Path):
    return isinstance(path[-1], Close)


def draw_oval(oval: Ellipse | Circle):
    coords = oval_coords(oval)
    if coords:
        canvas.create_oval(
            coords,
            fill=oval.fill.hex or '',
            outline=oval.stroke.hex or '',
            width=oval.stroke_width or ''
        )


def draw_rect(rect: Rect):
    coords = rect_coords(rect)
    if coords:
        canvas.create_rectangle(
            coords,
            fill=rect.fill.hex or '',
            outline=rect.stroke.hex or '',
            width=rect.stroke_width or ''
        )


def draw_path(path: Path):
    background_polygon_points: List[Tuple[float, float]] = []

    segment: PathSegment
    for segment in path.segments():
        if not segment.start or not segment.end:
            continue

        match segment:
            case Line() | Close():
                background_polygon_points.append(coords(segment.start)[0])
                background_polygon_points.append(coords(segment.end)[0])
                if not is_path_closed(path):
                    canvas.create_line(
                        coords(segment.start, segment.end),
                        fill=path.stroke.hex or '',
                        width=path.stroke_width or ''
                    )

    if not is_path_closed(path):
        canvas.create_polygon(
            background_polygon_points,
            fill=path.fill.hex or '',
        )
    else:
        canvas.create_polygon(
            background_polygon_points,
            fill=path.fill.hex or '',
            outline=path.stroke.hex or '',
            width=path.stroke_width or ''
        )


def draw_group(svg: Group):
    elem: SVGElement
    for elem in svg:
        match elem:
            case Path():
                draw_path(elem)
            case Rect():
                draw_rect(elem)
            case Circle() | Ellipse():
                draw_oval(elem)
            case Group():
                draw_group(elem)


def init_window():
    window = Tk(baseName='Screaming Sunrise', className='screaming sunrise')
    window.title('Screaming Sunrise')
    return window


def init_canvas(window: Tk):
    canvas = Canvas(window, bg='white', height=720, width=1280)
    canvas.pack()
    return canvas


args = sys.argv[1:]

if len(args) < 2:
    print('No command and/or path to svg file')
    sys.exit(1)

[command, path_to_svg] = args
svg: SVG = SVG.parse(path_to_svg)

window: Tk
canvas: Canvas

match command:
    case 'compile':
        print('No')
    case 'view':
        window = init_window()
        canvas = init_canvas(window)
        draw_group(svg)
        window.mainloop()
    case _:
        print(f'Unexpected first argument. Expected: "compile" or "view", got: {command}')
