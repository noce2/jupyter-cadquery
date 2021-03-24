from webcolors import name_to_rgb, hex_to_rgb, rgb_to_hex


class Color:
    def __init__(self, color=None):
        if color is None:
            self.r = self.g = self.b = 160
        elif isinstance(color, Color):
            self.r, self.g, self.b = color.r, color.g, color.b
        elif isinstance(color, str):
            if color[0] == "#":
                c = hex_to_rgb(color)
            else:
                c = name_to_rgb(color)
            self.r = c.red
            self.g = c.green
            self.b = c.blue
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            if all((isinstance(c, float) and (c <= 1.0) and (c >= 0.0)) for c in color):
                self.r, self.g, self.b = (int(c * 255) for c in color)
            elif all((isinstance(c, int) and (c <= 255) and (c >= 0)) for c in color):
                self.r, self.g, self.b = color
            else:
                self._invalid(color)
        else:
            self._invalid(color)

    def __str__(self):
        return f"Color({self.r}, {self.g}, {self.b})"

    def _invalid(self, color):
        print(f"warning: {color} is an invalid color, using grey (#aaa)")
        self.r = self.g = self.b = 160

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def percentage(self):
        return (self.r / 255, self.g / 255, self.b / 255)

    @property
    def web_color(self):
        return rgb_to_hex((self.r, self.g, self.b))
