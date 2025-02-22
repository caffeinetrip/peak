import json

import pygame

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = []

class Tilemap:
    def __init__(self, tile_size=16):
        self.tile_size = tile_size
        self.tilemap = {}
        self.decor_tiles = []
        
        self.tiles = {}
    
    def tile_exists(self, x, y):
        
        if f"{x}|{y}" in self.tilemap or f"{x};{y}" in self.tilemap:
            return True
        
        return False
    
    def tiles_around(self, pos, dot):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + dot + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size}, f)
        f.close()
        
    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        
    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['tile_id'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]
    
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos, ';'):
            if tile['tile_id'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def render(self, surf, decorations_surf, tileset, rotate_tiles, offset=(0, 0)):
            
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                physics_loc = str(x) + ';' + str(y)
                decor_loc = str(x) + ':' + str(y)
                background_loc = str(x) + '|' + str(y)
                
                   
                if background_loc in self.tilemap:
                    tile = self.tilemap[background_loc]
                    
                    if background_loc in rotate_tiles:
                        surf.blit((pygame.transform.rotate(tileset[tile['tile_id']], rotate_tiles[f'{tile['pos'][0]}|{tile['pos'][1]}'])), (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))     
                    else:
                        surf.blit(tileset[tile['tile_id']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))     
                    
                
                if physics_loc in self.tilemap:
                    tile = self.tilemap[physics_loc]
                    if not tile['tile_id'] in PHYSICS_TILES:
                        PHYSICS_TILES.append(tile['tile_id'])
                        
                    surf.blit(tileset[tile['tile_id']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
                    
                if decor_loc in self.tilemap:
                    tile = self.tilemap[decor_loc]
            
                    decorations_surf.blit(tileset[tile['tile_id']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))

class DangerBlock:
    def __init__(self, game, pos, angle):
        self.angle = angle
        self.pos = list(pos)
        self.animation = game.animations['danger_block/create'].copy()
        self.duration = self.animation.img_duration
        self.timer = 0

    def update(self):
        self.timer += 0.1
        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        if self.timer < self.duration:
            pygame.draw.rect(surf, (0, 0, 0), (self.pos[0] * 16 - offset[0], self.pos[1] * 16 - offset[1], 16, 16))
            surf.blit(pygame.transform.rotate(self.animation.img(), self.angle), 
                      (self.pos[0] * 16 - offset[0], self.pos[1] * 16 - offset[1]))