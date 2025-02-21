import pygame
from scripts.utils import lerp

class PhysicsEntity():
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')
        self.buffs = {}
        self.last_movement = [0, 0]
        self.death = False

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.animations[self.type + '/' + self.action].copy()
            
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement

        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
        
        self.animation.update()
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), 
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1] + 2))

class DangerBlockAnimation:
    def __init__(self, game, pos, angle):
        self.game = game
        self.angle = angle
        self.pos = list(pos)
        self.animation = self.game.animations['danger_block/create'].copy()
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

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.was_falling = False
        self.move_speed = 0.1
        self.on_edge = False
        self.land_timer = 0
        self.deaths_count = 0
        self.dash_duration = 20
        self.dash_speed = 3.0
        self.dashing = False
        self.death_animation_played = False
        self.last_tile = None
        self.tile = None
        self.danger_block_animations = []
        self.angle = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.death:
            if not self.death_animation_played:
                self.set_action('death')
                self.death_animation_played = True
            self.animation.update()
            super().update(tilemap)
            return
        
        super().update(tilemap, movement=movement)

        self.air_time += 1
        last_direction = None 

        if not hasattr(self, 'last_collision_direction'):
            self.last_collision_direction = None

        for direction in ['down', 'up', 'left', 'right']:
            if self.collisions[direction]:
                check_pos = self.pos[:]
                if direction == 'down':
                    check_pos[1] += self.size[1]
                elif direction == 'up':
                    check_pos[1] -= 1
                elif direction == 'left':
                    check_pos[0] -= 1
                elif direction == 'right':
                    check_pos[0] += self.size[0]

                self.tile = tilemap.solid_check(check_pos)
                self.last_collision_direction = direction

                if self.tile:
                    if self.tile['tile_id'] in ['32', '40']:
                        self.death = True
                        self.game.transition = 30
                        self.game.death_timer = 0 
                        return

        for direction in ['down', 'up', 'left', 'right']:
            if self.collisions[direction]:
                if last_direction is None:
                    last_direction = direction

        if self.last_tile:
            if (self.last_tile['tile_id'] == '38' and self.last_tile != self.tile) or (self.last_tile['tile_id'] == '38' and self.velocity[1] <= -2.5):
                original_pos = self.last_tile['pos'].copy()
                tile_loc = f"{original_pos[0]};{original_pos[1]}"
                if tile_loc in tilemap.tilemap:
                    tilemap.tilemap[tile_loc]['tile_id'] = '40'

                directions = [(0, -1, 0), (0, 1, 180), (1, 0, 270), (-1, 0, 90)]
                for dx, dy, dir_angle in directions:
                    check_pos = (original_pos[0] + dx, original_pos[1] + dy)
                    check_loc = f"{check_pos[0]}|{check_pos[1]}"
                    if not tilemap.tile_exists(check_pos[0], check_pos[1]):
                        tilemap.tilemap[check_loc] = {'tile_id': '16', 'pos': list(check_pos)}
                        self.game.rotate_tiles[check_loc] = dir_angle
                        self.danger_block_animations.append(DangerBlockAnimation(self.game, check_pos, dir_angle))

        self.last_tile = self.tile

        for anim in self.danger_block_animations:
            anim.update()
        self.danger_block_animations = [anim for anim in self.danger_block_animations if anim.timer < anim.duration]

        if self.dashing:
            self.dash_timer -= 1
            self.velocity[1] = 0.3
            if self.dash_timer <= 0:
                self.dashing = False
                self.velocity[0] = 0 
        else:
            if self.action == 'land':
                self.land_timer -= 1
                if self.land_timer <= 0:
                    self.land_timer = 0

            if self.collisions['down']:
                if self.was_falling:
                    self.set_action('land')
                    self.was_falling = False
                    self.land_timer = 10
                self.air_time = 0
                self.jumps = 1
            else:
                if self.velocity[1] > 0.5:
                    self.was_falling = True
                    self.set_action('fall')

            self.wall_slide = False
            if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
                self.wall_slide = True
                self.velocity[1] = min(self.velocity[1], 0.5)
                self.flip = self.collisions['left']
                self.set_action('wall_slide')

            if self.collisions['down'] and movement[0] == 0:
                left_point = (self.pos[0], self.pos[1] + self.size[1] + 1)
                right_point = (self.pos[0] + self.size[0], self.pos[1] + self.size[1] + 1)
                left_has_tile = any(rect.collidepoint(left_point) for rect in tilemap.physics_rects_around(self.pos))
                right_has_tile = any(rect.collidepoint(right_point) for rect in tilemap.physics_rects_around(self.pos))
                self.on_edge = not (left_has_tile and right_has_tile)

            if not self.wall_slide and self.land_timer == 0:
                if self.air_time > 4:
                    if self.was_falling:
                        self.set_action('fall')
                    else:
                        self.set_action('jump')
                elif movement[0] != 0:
                    self.set_action('run')
                    self.on_edge = False
                else:
                    self.set_action('edge_idle' if self.on_edge else 'idle')

        if movement[0] > 0 and not self.dashing:
            self.velocity[0] = min(self.velocity[0] + self.move_speed, self.move_speed)
        elif movement[0] < 0 and not self.dashing:
            self.velocity[0] = max(self.velocity[0] - self.move_speed, -self.move_speed)
        else:
            if self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - 0.1, 0)
            else:
                self.velocity[0] = min(self.velocity[0] + 0.1, 0)
                
        for anim in self.danger_block_animations:
            anim.render(self.game.main_surf, offset=self.game.render_scroll)
            
    def jump(self, jump_power=0):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0 or not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = 3.5 * (1 if self.flip else -1)
                self.velocity[1] = -2.5 + jump_power
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                if 'x2jump' in self.buffs:
                    self.buffs['x2jump'].ui.clear_buff()
                return True    
        elif self.jumps and self.action in ['idle', 'run', 'land']:
            self.velocity[1] = -3.0 + jump_power
            self.jumps -= 1
            self.air_time = 5
            if 'x2jump' in self.buffs:
                self.buffs['x2jump'].ui.clear_buff()
            return True
    
    def dash(self):
        self.dashing = True
        self.dash_timer = self.dash_duration
        self.velocity[0] = self.dash_speed * (-1 if self.flip else 1) 
        return True
    
    def render(self, surf, offset=(0, 0)):
        if self.death and self.animation.done:
            return 
        
        def process_sprite(color_map):
            sprite = self.animation.img()
            sprite_copy = sprite.copy()
            width, height = sprite_copy.get_size()
            for x in range(width):
                for y in range(height):
                    r, g, b, a = sprite_copy.get_at((x, y))
                    if (r, g, b) in color_map:
                        sprite_copy.set_at((x, y), (*color_map[(r, g, b)], a))
            return sprite_copy

        color_maps = {'x2jump': {(255, 0, 0): (255, 179, 41)}}

        for buff, color_map in color_maps.items():
            if buff in self.buffs:
                processed_sprite = process_sprite(color_map)
                surf.blit(pygame.transform.flip(processed_sprite, self.flip, False),
                          (self.pos[0] - offset[0] + self.anim_offset[0],
                           self.pos[1] - offset[1] + self.anim_offset[1] + 2))
                return

        super().render(surf, offset=offset)