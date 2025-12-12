from board import DISPLAY as display
import displayio


général = displayio.Group(scale=1,x=0,y=0)
display.show(général)

class rectangle:
    def __init__(self, x=0,y=0,color=0xFF0000, width=20, height=20, scale=1, hidden=False):
        
        
        self.bitmap = displayio.Bitmap(width, height, 1)

        self.palette = displayio.Palette(1)
        self.palette[0] = color

        self.dir = 0
        
        tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.palette,width=width,height=height, tile_width=1, tile_height=1)
        tile_grid.hidden = hidden
       
        self.group = displayio.Group(scale=scale,x=x,y=y)

        self.group.insert(0,tile_grid)
        général.append(self.group)
        
    
    @property
    def x(self):
        return self.group.x
    @x.setter
    def x(self, x):
        self.group.x = x
    
    @property
    def y(self):
        return self.group.y
    @y.setter
    def y(self, y):
        self.group.y = y

    @property
    def color(self):
        return self.group[0].pixel_shader[0]
    @color.setter
    def color(self, color):
        self.palette[0] = color

    @property
    def width(self):
        return self.bitmap.width

    @width.setter
    def width(self, width):
        hidden = self.group[0].hidden
        self.group.remove(self.group[0])
        self.bitmap = displayio.Bitmap(width, self.bitmap.height, 1)
        tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.palette,width=width,height=self.bitmap.height, tile_width=1, tile_height=1)
        tile_grid.hidden = hidden
        self.group.insert(0,tile_grid)

    @property
    def height(self):
        return self.bitmap.height

    @height.setter
    def height(self, height):
        hidden = self.group[0].hidden
        self.group.remove(self.group[0])
        self.bitmap = displayio.Bitmap(self.bitmap.width, height, 1)
        tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.palette,width=self.bitmap.width,height=height, tile_width=1, tile_height=1)
        tile_grid.hidden = hidden
        self.group.insert(0,tile_grid)

    @property
    def scale(self):
        return self.group.scale
    @scale.setter
    def scale(self, scale):
        self.group.scale = scale

    @property
    def hidden(self):
        return self.group[0].hidden
    @hidden.setter
    def hidden(self, hidden):
        self.group[0].hidden = hidden

    @property
    def direction(self):
        return self.dir
    @direction.setter
    def direction(self, direction):
        self.dir =((direction//45)*45)%360

    def moveBy(self, inc):
        nx = 1
        ny = 1
        if self.direction == 0:
            ny=0
            nx=1
        elif self.direction == 45:
            ny=1
            nx=1
        elif self.direction == 90:
            ny=1
            nx=0
        elif self.direction == 135:
            ny=1
            nx=-1
        elif self.direction == 180:
            ny= 0
            nx =-1
        elif self.direction == 225:
            ny = -1
            nx = -1
        elif self.direction == 270:
            ny = -1
            nx = 0
        elif self.direction == 315:
            ny = -1
            nx = 1
        self.y += ny*inc
        self.x += nx*inc

    def bounceIfEdge(self, borders="nesw"):
        hit_n = "n" in borders and border_collision("n", self)
        hit_s = "s" in borders and border_collision("s", self)
        hit_e = "e" in borders and border_collision("e", self)
        hit_w = "w" in borders and border_collision("w", self)

        hit_horizontal = hit_n or hit_s
        hit_vertical = hit_e or hit_w

        if hit_horizontal and hit_vertical:
            self.direction = (self.direction + 180) % 360
        elif hit_horizontal:
            self.direction = (360 - self.direction) % 360
        elif hit_vertical:
            self.direction = (180 - self.direction) % 360

        if hit_n:
            self.y = 0
        if hit_s:
            self.y = display.height - self.height * self.scale
        if hit_w:
            self.x = 0
        if hit_e:
            self.x = display.width - self.width * self.scale

    def bounceIfObject(self, other, borders="nesw"):
        if not collision(self, other):
            return False

        self_center_x = self.x + (self.width * self.scale) / 2
        self_center_y = self.y + (self.height * self.scale) / 2
        other_center_x = other.x + (other.width * other.scale) / 2
        other_center_y = other.y + (other.height * other.scale) / 2

        dx = self_center_x - other_center_x
        dy = self_center_y - other_center_y

        overlap_x = (self.width * self.scale + other.width * other.scale) / 2 - abs(dx)
        overlap_y = (self.height * self.scale + other.height * other.scale) / 2 - abs(dy)

        if overlap_x < overlap_y:
            if "e" in borders or "w" in borders:
                self.direction = (180 - self.direction) % 360
                if dx > 0:
                    self.x = other.x + other.width * other.scale
                else:
                    self.x = other.x - self.width * self.scale
        else:
            if "n" in borders or "s" in borders:
                self.direction = (360 - self.direction) % 360
                if dy > 0:
                    self.y = other.y + other.height * other.scale
                else:
                    self.y = other.y - self.height * self.scale

        return True



class image:
    def __init__(self, x=0,y=0, scale=1, path="/thingz.bmp",hidden=False):

        file = open(path, "rb")
        self.bitmap = displayio.OnDiskBitmap(file)

        tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.bitmap.pixel_shader)
        tile_grid.hidden = hidden
        self.group = displayio.Group(scale=scale,x=x,y=y)
        self.group.insert(0,tile_grid)

        self.dir = 0
        
        général.append(self.group)
    
    @property
    def x(self):
        return self.group.x
    @x.setter
    def x(self, x):
        self.group.x = x
    
    @property
    def y(self):
        return self.group.y
    @y.setter
    def y(self, y):
        self.group.y = y

    @property
    def scale(self):
        return self.group.scale
    @scale.setter
    def scale(self, scale):
        self.group.scale = scale
    
    @property
    def hidden(self):
        return self.group[0].hidden
    @hidden.setter
    def hidden(self, hidden):
        self.group[0].hidden = hidden

    @property
    def height(self):
        return self.bitmap.height
    
    @property
    def width(self):
        return self.bitmap.width

    @property
    def direction(self):
        return self.dir
    @direction.setter
    def direction(self, direction):
        self.dir =((direction//45)*45)%360

    def moveBy(self, inc):
        nx = 1
        ny = 1
        if self.direction == 0:
            ny=0
            nx=1
        elif self.direction == 45:
            ny=1
            nx=1
        elif self.direction == 90:
            ny=1
            nx=0
        elif self.direction == 135:
            ny=1
            nx=-1
        elif self.direction == 180:
            ny= 0
            nx =-1
        elif self.direction == 225:
            ny = -1
            nx = -1
        elif self.direction == 270:
            ny = -1
            nx = 0
        elif self.direction == 315:
            ny = -1
            nx = 1
        
        self.y += ny*inc
        self.x += nx*inc

    def bounceIfEdge(self, borders="nesw"):
        hit_n = "n" in borders and border_collision("n", self)
        hit_s = "s" in borders and border_collision("s", self)
        hit_e = "e" in borders and border_collision("e", self)
        hit_w = "w" in borders and border_collision("w", self)

        hit_horizontal = hit_n or hit_s
        hit_vertical = hit_e or hit_w

        if hit_horizontal and hit_vertical:
            self.direction = (self.direction + 180) % 360
        elif hit_horizontal:
            self.direction = (360 - self.direction) % 360
        elif hit_vertical:
            self.direction = (180 - self.direction) % 360

        if hit_n:
            self.y = 0
        if hit_s:
            self.y = display.height - self.height * self.scale
        if hit_w:
            self.x = 0
        if hit_e:
            self.x = display.width - self.width * self.scale

    def bounceIfObject(self, other, borders="nesw"):
        if not collision(self, other):
            return False

        self_center_x = self.x + (self.width * self.scale) / 2
        self_center_y = self.y + (self.height * self.scale) / 2
        other_center_x = other.x + (other.width * other.scale) / 2
        other_center_y = other.y + (other.height * other.scale) / 2

        dx = self_center_x - other_center_x
        dy = self_center_y - other_center_y

        overlap_x = (self.width * self.scale + other.width * other.scale) / 2 - abs(dx)
        overlap_y = (self.height * self.scale + other.height * other.scale) / 2 - abs(dy)

        if overlap_x < overlap_y:
            if "e" in borders or "w" in borders:
                self.direction = (180 - self.direction) % 360
                if dx > 0:
                    self.x = other.x + other.width * other.scale
                else:
                    self.x = other.x - self.width * self.scale
        else:
            if "n" in borders or "s" in borders:
                self.direction = (360 - self.direction) % 360
                if dy > 0:
                    self.y = other.y + other.height * other.scale
                else:
                    self.y = other.y - self.height * self.scale

        return True



class icon:
    def __init__(self, x=0,y=0, scale=1, name="cross",color=0xFFFFFF, hidden=False):
        path = "/lib/sprites/icons/"+name+".bmp"
        file = open(path, "rb")

        self.bitmap = displayio.OnDiskBitmap(file)
        self.new_palette = displayio.Palette(2)
        self.new_palette[0] = color

        tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.new_palette)
        tile_grid.hidden = hidden
        self.group = displayio.Group(scale=scale,x=x,y=y)
        self.group.insert(0,tile_grid)

        self.dir = 0
        
        général.append(self.group)
    
    @property
    def x(self):
        return self.group.x
    @x.setter
    def x(self, x):
        self.group.x = x
    
    @property
    def y(self):
        return self.group.y
    @y.setter
    def y(self, y):
        self.group.y = y

    @property
    def scale(self):
        return self.group.scale
    @scale.setter
    def scale(self, scale):
        self.group.scale = scale
    
    @property
    def hidden(self):
        return self.group[0].hidden
    @hidden.setter
    def hidden(self, hidden):
        self.group[0].hidden = hidden

    @property
    def height(self):
        return self.bitmap.height
    
    @property
    def width(self):
        return self.bitmap.width

    @property
    def color(self):
        return self.new_palette[0]
    @color.setter
    def color(self, color):
        self.new_palette[0] = color

    @property
    def direction(self):
        return self.dir
    @direction.setter
    def direction(self, direction):
        self.dir =((direction//45)*45)%360

    def moveBy(self, inc):
        nx = 1
        ny = 1
        if self.direction == 0:
            ny=0
            nx=1
        elif self.direction == 45:
            ny=1
            nx=1
        elif self.direction == 90:
            ny=1
            nx=0
        elif self.direction == 135:
            ny=1
            nx=-1
        elif self.direction == 180:
            ny= 0
            nx =-1
        elif self.direction == 225:
            ny = -1
            nx = -1
        elif self.direction == 270:
            ny = -1
            nx = 0
        elif self.direction == 315:
            ny = -1
            nx = 1
        self.y += ny*inc
        self.x += nx*inc

    def bounceIfEdge(self, borders="nesw"):
        hit_n = "n" in borders and border_collision("n", self)
        hit_s = "s" in borders and border_collision("s", self)
        hit_e = "e" in borders and border_collision("e", self)
        hit_w = "w" in borders and border_collision("w", self)

        hit_horizontal = hit_n or hit_s
        hit_vertical = hit_e or hit_w

        if hit_horizontal and hit_vertical:
            self.direction = (self.direction + 180) % 360
        elif hit_horizontal:
            self.direction = (360 - self.direction) % 360
        elif hit_vertical:
            self.direction = (180 - self.direction) % 360

        if hit_n:
            self.y = 0
        if hit_s:
            self.y = display.height - self.height * self.scale
        if hit_w:
            self.x = 0
        if hit_e:
            self.x = display.width - self.width * self.scale

    def bounceIfObject(self, other, borders="nesw"):
        if not collision(self, other):
            return False

        self_center_x = self.x + (self.width * self.scale) / 2
        self_center_y = self.y + (self.height * self.scale) / 2
        other_center_x = other.x + (other.width * other.scale) / 2
        other_center_y = other.y + (other.height * other.scale) / 2

        dx = self_center_x - other_center_x
        dy = self_center_y - other_center_y

        overlap_x = (self.width * self.scale + other.width * other.scale) / 2 - abs(dx)
        overlap_y = (self.height * self.scale + other.height * other.scale) / 2 - abs(dy)

        if overlap_x < overlap_y:
            if "e" in borders or "w" in borders:
                self.direction = (180 - self.direction) % 360
                if dx > 0:
                    self.x = other.x + other.width * other.scale
                else:
                    self.x = other.x - self.width * self.scale
        else:
            if "n" in borders or "s" in borders:
                self.direction = (360 - self.direction) % 360
                if dy > 0:
                    self.y = other.y + other.height * other.scale
                else:
                    self.y = other.y - self.height * self.scale

        return True


def collision(a,b):
  
    if (a.x+a.width*a.scale) > b.x and (b.x+b.width*b.scale) > a.x:
        if (a.y+a.height*a.scale) > b.y and (b.y+b.height*b.scale) > a.y :
            return True
        else:
            return False        
    else:
        return False

def border_collision(border,sprite):
    if border=='n':
        return sprite.y <= 0
    if border=='s':
        return (sprite.y+sprite.height*sprite.scale) >= display.height
    if border=='w':
        return sprite.x <= 0
    if border=='e':
        return (sprite.x+sprite.width*sprite.scale) >= display.width
    return False

def version():
    return "1.0.4"

