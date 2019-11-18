from PIL import Image
from math import sqrt

def all_channels(func):
    def wrapper(channel, *args, **kwargs):
        try:
            return func(channel, *args, **kwargs)
        except TypeError:
            return tuple(func(c, *args, **kwargs) for c in channel)
    return wrapper

@all_channels
def to_sRGB_f(x):
    ''' Returns a sRGB value in the range [0,1]
        for linear input in [0,1].
    '''
    return 12.92*x if x <= 0.0031308 else (1.055 * (x ** (1/2.4))) - 0.055

@all_channels
def to_sRGB(x):
    ''' Returns a sRGB value in the range [0,255]
        for linear input in [0,1]
    '''
    return int(255.9999 * to_sRGB_f(x))

@all_channels
def from_sRGB(x):
    ''' Returns a linear value in the range [0,1]
        for sRGB input in [0,255].
    '''
    x /= 255.0
    if x <= 0.04045:
        y = x / 12.92
    else:
        y = ((x + 0.055) / 1.055) ** 2.4
    return y

def all_channels2(func):
    def wrapper(channel1, channel2, *args, **kwargs):
        try:
            return func(channel1, channel2, *args, **kwargs)
        except TypeError:
            return tuple(func(c1, c2, *args, **kwargs) for c1,c2 in zip(channel1, channel2))
    return wrapper

@all_channels2
def lerp(color1, color2, frac):
    return color1 * (1 - frac) + color2 * frac



def perceptual_steps(color1, color2, steps):
    gamma = .43
    color1_lin = from_sRGB(color1)
    bright1 = sum(color1_lin)**gamma
    color2_lin = from_sRGB(color2)
    bright2 = sum(color2_lin)**gamma
    for step in range(steps):
        intensity = lerp(bright1, bright2, step, steps) ** (1/gamma)
        color = lerp(color1_lin, color2_lin, step, steps)
        if sum(color) != 0:
            color = [c * intensity / sum(color) for c in color]
        color = to_sRGB(color)
        yield color

class Line:
    ''' Defines a line of the form ax + by + c = 0 '''
    def __init__(self, a, b, c=None):
        if c is None:
            x1,y1 = a
            x2,y2 = b
            a = y2 - y1
            b = x1 - x2
            c = x2*y1 - y2*x1
        self.a = a
        self.b = b
        self.c = c
        self.distance_multiplier = 1.0 / sqrt(a*a + b*b)

    def distance(self, x, y):
        ''' Using the equation from
            https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_an_equation
            modified so that the distance can be positive or negative depending
            on which side of the line it's on.
        '''
        return (self.a * x + self.b * y + self.c) * self.distance_multiplier

class PerceptualGradient:
    GAMMA = .43
    def __init__(self, color1, color2):
        self.color1_lin = from_sRGB(color1)
        self.bright1 = sum(self.color1_lin)**self.GAMMA
        self.color2_lin = from_sRGB(color2)
        self.bright2 = sum(self.color2_lin)**self.GAMMA

    def color(self, t):
        ''' Return the gradient color for a parameter in the range [0.0, 1.0].
        '''
        intensity = lerp(self.bright1, self.bright2, t) ** (1/self.GAMMA)
        col = lerp(self.color1_lin, self.color2_lin, t)
        total = sum(col)
        if total != 0:
            col = [c * intensity / total for c in col]
        col = to_sRGB(col)
        return col

def fill_gradient(im, gradient_color, line_distance=None, max_distance=None):
    w, h = im.size
    if line_distance is None:
        def line_distance(x, y):
            return x - ((w-1) / 2.0) # vertical line through the middle
    ul = line_distance(0, 0)
    ur = line_distance(w-1, 0)
    ll = line_distance(0, h-1)
    lr = line_distance(w-1, h-1)
    if max_distance is None:
        low = min([ul, ur, ll, lr])
        high = max([ul, ur, ll, lr])
        max_distance = min(abs(low), abs(high))
    pix = im.load()
    for y in range(h):
        for x in range(w):
            dist = line_distance(x, y)
            ratio = 0.5 + 0.5 * dist / max_distance
            ratio = max(0.0, min(1.0, ratio))
            if ul > ur: ratio = 1.0 - ratio
            pix[x, y] = gradient_color(ratio)

def main():
  w, h = 406, 101
  im = Image.new('RGB', [w, h])
  line = Line([w/2 - h/2, 0], [w/2 + h/2, h-1])
  grad = PerceptualGradient([252, 13, 27], [41, 253, 46])
  fill_gradient(im, grad.color, line.distance, 71)
  im.save("out.png")
  print("saved to out.png")

main()