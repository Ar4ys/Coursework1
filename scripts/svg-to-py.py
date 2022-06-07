import sys
from typing import List, Tuple, Any
from svgelements import SVG, Path, PathSegment, Line, Close, Point, Rect, Circle, Ellipse, SVGElement, Group
from tkinter import Tk, Canvas

SimplePoint = Tuple[float | int, float | int]


class Printer:
    indent_symbol = ' '
    indent_size = 4
    indent = 0
    buffer = ''

    parse_coords_int = True
    print_fun_in_line = True
    with_tkinter = True

    def print_svg(self, svg: SVG):
        if self.with_tkinter:
            self.print_tk_init()
        self.print_helpers()
        self.print_group(svg)
        if self.with_tkinter:
            self.print_tk_mainloop()

        return self.buffer


    def print_group(self, group: Group):
        self.print_def(group.id)

        is_empty = True

        elem: SVGElement
        for elem in group:
            match elem:
                case Path():
                    is_empty = False
                    self.print_path(elem)
                case Rect():
                    is_empty = False
                    self.print_rect(elem)
                case Circle() | Ellipse():
                    is_empty = False
                    self.print_oval(elem)
                case Group():
                    is_empty = False
                    self.print_group(elem)

        if is_empty:
            self.print('pass')

        self.indent_down()
        self.print(f'{group.id}()')

    def print_rect(self, rect: Rect):
        coords = rect_coords(rect)

        if not coords:
            return

        self.print_simple_2d(
            'draw_rect',
            coords=coords,
            fill=rect.fill.hex,
            outline=rect.stroke.hex,
            width=rect.stroke_width
        )

    def print_oval(self, oval: Ellipse | Circle):
        coords = oval_coords(oval)

        if not coords:
            return

        self.print_simple_2d(
            'draw_oval',
            coords=coords,
            fill=oval.fill.hex,
            outline=oval.stroke.hex,
            width=oval.stroke_width
        )

    def print_simple_2d(
        self,
        name: str,
        coords: Tuple[SimplePoint, ...],
        fill: str | None = None,
        outline: str | None = None,
        width: float | None = None
    ):
        to_print = f'{name}('
        coords = int_coords(coords) if self.parse_coords_int else coords

        if not fill and not outline and not width:
            to_print += f'{coords})'
            self.print(to_print)
            return

        if self.print_fun_in_line:
            to_print += f'{coords}'
            to_print += f", fill='{fill}'" if fill else ''
            if outline:
                to_print += f", outline='{outline}'" if outline not in ('#000', '#000000') else ''
                to_print += f', width={width}' if width else ''
            to_print += f')'
            self.print(to_print)
        else:
            self.print(to_print)
            self.indent_up()
            self.print(
                f'{coords},',
                f"fill='{fill}'," if fill else None,
            )
            if outline:
                self.print(
                    f"outline='{outline}'," if outline not in ('#000', '#000000') else None,
                    f'width={width},' if width else None
                )
            self.indent_down()
            self.print(')')

    def print_path(self, path: Path):
        if is_path_closed(path):
            self.print_polygon(path)
        else:
            self.print_simple_2d(
                'draw_path',
                path_coords(path),
                outline=path.stroke.hex,
                width=path.stroke_width,
            )

    def print_tk_init(self):
        self.print_split_lines("""
from tkinter import Tk, Canvas
from typing import Tuple

window = Tk(baseName='Svg-To-Py', className='svg-to-py')
window.title('Svg-To-Py')
canvas = Canvas(window, bg='white', height=720, width=1280)
canvas.pack()
""")

    def print_tk_mainloop(self):
        self.print('window.mainloop()')

    def print_helpers(self):
        self.print_split_lines("""
def draw_oval(
    coords: Tuple[Tuple[float, float], ...],
    fill: str | None = None,
    outline: str | None = None,
    width: float | None = None
):
    canvas.create_oval(
        coords,
        fill=fill or '',
        outline=outline or '#000',
        width=width or 0
    )


def draw_rect(
    coords: Tuple[Tuple[float, float], ...],
    fill: str | None = None,
    outline: str | None = None,
    width: float | None = None
):
    canvas.create_rectangle(
        coords,
        fill=fill or '',
        outline=outline or '#000',
        width=width or 0
    )


def draw_polygon(
    coords: Tuple[Tuple[float, float], ...],
    fill: str | None = None,
    outline: str | None = None,
    width: float | None = None
):
    outline = outline or ('#000' if width else '')
    canvas.create_polygon(
        coords,
        fill=fill or '',
        outline=outline,
        width=width or 0
    )


def draw_path(
    coords: Tuple[Tuple[float, float], ...],
    outline: str | None = None,
    width: float | None = None
):
    for (i, point) in enumerate(coords):
        if i == 0:
            continue

        canvas.create_line(
            (coords[i - 1], point),
            fill=outline or '#000',
            width=width or ''
        )
""")

    def print_line(
        self,
        coords: Tuple[SimplePoint, SimplePoint],
        fill: str | None = None,
        width: float | None = None
    ):
        self.print_simple_2d(
            'canvas.create_line',
            coords,
            fill=fill,
            width=width,
        )

    def print_polygon(self, path: Path):
        coords = path_coords(path)

        if not coords:
            return

        self.print_simple_2d(
            'draw_polygon',
            coords=coords,
            fill=path.fill.hex,
            outline=path.stroke.hex,
            width=path.stroke_width
        )

    def print_def(self, name, *params: str):
        fun_def = f'def {name}('

        if len(params) < 3:
            for param in params:
                fun_def += f'{param}'

            fun_def += f'):'
            self.print(fun_def)
            self.indent_up()
            return

        self.print(fun_def)
        self.indent_up()

        for (i, param) in enumerate(params):
            comma = ',' if i != len(params) - 1 else ''
            self.print(param + comma)

        self.indent_down()
        self.print('):')
        self.indent_up()

    def indent_set(self, value: int):
        self.indent = value

    def indent_up(self):
        self.indent += 1

    def indent_down(self):
        self.indent -= 1

    def print(self, *strings: str | None):
        indent = self.indent_symbol * self.indent_size * self.indent
        for string in strings:
            if string:
                self.buffer += indent + string + '\n'

    def print_split_lines(self, string: str):
        for line in string.splitlines():
            self.print(line)

def coords(*args: Point | Tuple[float, float]):
    return tuple(map(lambda x: (x[0], x[1]), args))


def int_coords(coords: SimplePoint | Tuple[SimplePoint | Tuple[SimplePoint, ...], ...]) -> Any:
    return tuple(map(lambda x: int_coords(x) if isinstance(x, Tuple) else int(x), coords))


def path_coords(path: Path, closed=False):
    path_points: List[Tuple[float, float]] = []
    segments: List[PathSegment] = path.segments()
    for (i, segment) in enumerate(segments):
        match segment:
            case Line() | Close():
                if len(path_points) == 0:
                    path_points.append(coords(segment.start or Point(0, 0))[0])

                if closed and i == len(segments) - 1:
                    continue

                path_points.append(coords(segment.end or Point(0, 0))[0])

    return tuple(path_points)

def rect_coords(rect: Rect):
    if not rect.width or not rect.height:
        return None

    x = rect.x or 0
    y = rect.y or 0
    return (x, y), (x + rect.width, y + rect.height)


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
printer: Printer

match command:
    case 'compile':
        printer = Printer()
        print(printer.print_svg(svg))
    case 'view':
        window = init_window()
        canvas = init_canvas(window)
        draw_group(svg)
        window.mainloop()
    case _:
        print(f'Unexpected first argument. Expected: "compile" or "view", got: {command}')
