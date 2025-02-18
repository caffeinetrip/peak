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
        self.spawn_point = [180, 100]
    
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

                tile = tilemap.solid_check(check_pos)
                if tile:
                    if tile['tile_id'] == '32':
                        self.death = True
                        self.game.transition = 30
                        self.game.death_timer = 0 
                        return
                    elif tile['tile_id'] == '38':
                        pass

        if self.dashing:
            self.dash_timer -= 1
            self.velocity[1] = 0 
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

    def jump(self, jump_power=0):
        
        if 'x2jump' in self.buffs:
            self.buffs['x2jump'].ui.clear_buff()
        
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0 or not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = 3.5 * (1 if self.flip else -1)
                self.velocity[1] = -2.5 + jump_power
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True    
            
        elif self.jumps and self.action in ['idle', 'run', 'land']:
            self.velocity[1] = -3.0 + jump_power
            self.jumps -= 1
            self.air_time = 5
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

        color_maps = {
            'x2jump': {(255, 0, 0): (255, 179, 41)},
        }

        for buff, color_map in color_maps.items():
            if buff in self.buffs:
                processed_sprite = process_sprite(color_map)
                surf.blit(
                    pygame.transform.flip(processed_sprite, self.flip, False),
                    (
                        self.pos[0] - offset[0] + self.anim_offset[0],
                        self.pos[1] - offset[1] + self.anim_offset[1] + 2,
                    ),
                )
                return

        super().render(surf, offset=offset)