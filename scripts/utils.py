import os

import pygame


def load_image(path):
    img = pygame.image.load(path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def lerp(a, b, t):
    return a + (b - a) * t
class Tileset():
    def __init__(self, tileset, tile_size):
        self.tileset = tileset
        self.tile_size = tile_size
        self.tileset_image = pygame.image.load(self.tileset).convert()
        self.tileset_image.set_colorkey((0, 0, 0))
        
    def load_tileset(self):

        tileset_width, tileset_height = self.tileset_image.get_size()
    
        tiles = {}
        tile_count = '-1'
        for y in range(0, tileset_height, self.tile_size):
            for x in range(0, tileset_width, self.tile_size):
                tile_count = f'{int(tile_count)+1}'
                
                tile = self.tileset_image.subsurface(pygame.Rect(x, y, self.tile_size, self.tile_size))
                tiles[tile_count] = tile

        return tiles

class Animation:
    def __init__(self, path, img_dur=5, loop=True, img_size=16):
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
        self.img_size = img_size
        self.path = path
        self.images = self.load_frames()
    
    def copy(self):
        return Animation(self.path, self.img_duration, self.loop)
    
    def load_frames(self):
        image = load_image(self.path)
        image_width, image_height = pygame.image.load(self.path).convert().get_size()
    
        images = []
        for y in range(0, image_height, self.img_size):
            for x in range(0, image_width, self.img_size):
                img = image.subsurface(pygame.Rect(x, y, self.img_size, self.img_size))
                images.append(img)
        return images

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]