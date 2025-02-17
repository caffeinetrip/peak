import sys, pygame, random, math
from OpenGL import *
from scripts.utils import Animation, Tileset, load_image
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.ui import SkillsUI
from scripts.buff import *
from scripts.shaders import Shader
from scripts.particles import Particle, load_particle_images

screenshot_effect = False
effect_duration = 100 
effect_start_time = 0

class Game():
    def __init__(self):
        pygame.init()
        
        self.font = pygame.font.SysFont('data/texts/BoutiqueBitmap9x9_1.9.ttf', 24)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF)
        
        self.main_shader = Shader('shader', ['game_shader', 'ui_shader'])

        self.display_width, self.display_height = 384, 216
        
        self.display = pygame.Surface((self.display_width, self.display_height))

        self.main_surf = pygame.Surface((self.display_width, self.display_height))
        self.decoration_surf = pygame.Surface((self.display_width, self.display_height))
        self.ui_surf = pygame.Surface((960, 540))
        
        self.clock = pygame.time.Clock()
        self.movement = [False, False]

        self.noise_cof = 1.0
        
        self.screen_shake = 0 
        
        load_particle_images('data/assets/particles')
        
        self.animations = {
            'player/idle': Animation('data/assets/Animations/Player/idle/anim1.png', img_dur=30),
            'player/edge_idle': Animation('data/assets/Animations/Player/idle/anim2.png', img_dur=30),
            'player/run': Animation('data/assets/Animations/Player/walk/anim1.png', img_dur=6),
            'player/jump': Animation('data/assets/Animations/Player/jump/anim1.png', img_dur=7, loop=False),
            'player/wall_slide': Animation('data/assets/Animations/Player/slide/anim1.png'),
            'player/fall': Animation('data/assets/Animations/Player/fall/anim1.png'),
            'player/land': Animation('data/assets/Animations/Player/land/anim1.png', img_dur=20, loop=False),
            'player/dash': Animation('data/assets/Animations/Player/dash/anim1.png', img_dur=20, loop=False),
        }
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tileset = Tileset("data/assets/map_tiles/test_map/tileset.png", 16).load_tileset()
                
        self.tilemap = Tilemap(self, tile_size=16)
        
        self.particles = []
        
        self.level = 'map'
        self.load_level(self.level)
        
        self.ui = {
            'glitch_dash': SkillsUI(50,50, load_image('data/assets/spells/glitch_dash.png'), 400, 475, 4 , 'Q'),
            'glitch_jump': SkillsUI(50,50, load_image('data/assets/spells/glitch_jump.png'), 460, 475, 4, 'E'),
            'screenshot': SkillsUI(50,50, load_image('data/assets/spells/screenshot.png'), 520, 475, 6, 'F'),
        }
        
        pygame.display.set_caption('stupid-questions')
        
        self.t = 0
        
        self.screenshot_effect = False
        self.effect_duration = 250
        self.effect_start_time = 0
        
        self.button_conditions = {'glitch_dash': False, 'glitch_jump': False, 'screenshot': False}

        self.transition = 30 
        self.transition_speed = 1 
        
    def load_level(self, level_name):
        self.tilemap.load('data/levels/' + level_name + '.json')
        
        self.player.pos = [45, 100]
        self.player.air_time = 0
        
        self.scroll = [0, 0]
        
        self.screen_color = [0,0,0]

    def run(self):
        while True:
            self.t += self.clock.get_time() / 1000
            
            self.ui_surf.fill((0,0,0))
            self.main_surf.fill((0, 0, 0))
            self.decoration_surf.fill((0, 0, 0))
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 25
            self.scroll[1] += ((self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1])-25) / 25
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            mpos = pygame.mouse.get_pos()
            
            self.tilemap.render(
                self.main_surf,
                self.decoration_surf,
                self.tileset,
                offset=render_scroll,
            )
            
            tilemap_surf = self.main_surf.copy().convert_alpha()
            tilemap_surf.set_colorkey((0,0,0))

            if self.player.action == 'run':
                for i in range(random.randint(1,3)):
                    if random.randint(1,20) == 1:
                        
                        if random.randint(1,10) == 5:
                            particle_color = (51,51,51)
                        elif random.randint(1,25) == 5:
                            particle_color = (140,140,140)
                        else:
                            particle_color = self.main_surf.get_at((self.player.pos[0] + self.player.size[0] - self.scroll[0], self.player.pos[1] + self.player.size[1] - self.scroll[1] + 1))
                        
                        self.particles.append(
                            Particle(
                                self.player.pos[0] + self.player.size[0] // 2 + random.randint(-3, 3),
                                self.player.pos[1] + self.player.size[1]-1,
                                'grass', 
                                [self.player.velocity[0], -0.1],
                                0.5, 
                                0,
                                particle_color,
                                alpha=200
                            ))
                        
            if self.player.action == 'land':
                
                if self.screen_shake < 5:
                    self.screen_shake = 5
                
                for i in range(random.randint(1,2)):
                    if i == 1:
                        if random.randint(1,10) == 5:
                            particle_color = (51,51,51)
                        else:
                            particle_color = self.main_surf.get_at((self.player.pos[0] + self.player.size[0] - self.scroll[0], self.player.pos[1] + self.player.size[1] - self.scroll[1] + 1))
                        
                        if random.randint(1,2) == 1:
                            x = -1.2
                        else:
                            x = 1.2
                        
                        self.particles.append(
                            Particle(
                                self.player.pos[0] + self.player.size[0] // 2 + random.randint(-3, 3),
                                self.player.pos[1] + self.player.size[1]-1,
                                'grass', 
                                [x, -0.2],
                                0.5, 
                                0,
                                particle_color,
                                alpha=200
                            ))
            
            if self.player.action == 'jump':
                    
                if random.randint(1,int(50)) == 1:
                    self.particles.append(
                        Particle(
                            self.player.pos[0] + self.player.size[0] // 2 + random.randint(-3, 3),
                            self.player.pos[1] + self.player.size[1]-1,
                            'grass', 
                            [0, 1],
                            0.5, 
                            0,
                            (215,215,215),
                            alpha=200
                        ))

            if self.player.action == 'wall_slide':
                for i in range(random.randint(1,3)):
                    if random.randint(1,10) == 1:
                        particle_color = (140,140,140, 150)
                        if random.randint(1,10) == 5:
                            particle_color = (51,51,51, 150)
                    
                        if self.player.flip:
                            kef = -1.5
                        else:
                            kef = 2.7
                            
                        self.particles.append(
                            Particle(
                                self.player.pos[0] + self.player.size[0] // 2 + kef,
                                self.player.pos[1],
                                'grass', 
                                [0, (self.player.velocity[0]*-1)*2],
                                0.5, 
                                0,
                                particle_color,
                                alpha=200
                            ))
            
            if self.screen_shake > 0:
                self.screen_shake -= 1
                self.scroll[0] += random.randint((self.screen_shake//5) * -1, (self.screen_shake//5))
                self.scroll[1] += random.randint((self.screen_shake//5) * -1, (self.screen_shake//5))
                        
            for particle in self.particles[:]:
                particle.update(self.clock.get_time() / 45)
                
            for particle in self.particles:
                particle.draw(self.main_surf, self.scroll)
                
            self.main_surf.blit(tilemap_surf)
                
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.main_surf, offset=render_scroll)

            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display.blit(display_sillhouette, offset)
            
            for name, buff in self.player.buffs.items():
                buff.activate_effect()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        if 'x2jump' in self.player.buffs:
                            self.player.jump(-1.5)
                        else:
                            self.player.jump()
                        
                    if event.key == pygame.K_q and self.ui['glitch_dash'].active:
                        self.button_conditions['glitch_dash'] = True
                        self.player.dash()
                        self.ui['glitch_dash'].active = False
                        
                    if event.key == pygame.K_e and self.ui['glitch_jump'].active:
                        self.button_conditions['glitch_jump'] = True
                        self.player.buffs['x2jump'] = Buff('x2jump', 1.5, x2jump, self.player, load_image('data/assets/spells/glitch_jump.png'))
                        self.ui['glitch_jump'].active = False
                            
                    if event.key == pygame.K_f and self.ui['screenshot'].active:
                        self.button_conditions['screenshot'] = True
                        self.ui['screenshot'].active = False
                        self.screenshot_effect = True
                        self.effect_start_time = pygame.time.get_ticks()
                        
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                       self.button_conditions['glitch_dash'] = False
                    if event.key == pygame.K_e:
                        self.button_conditions['glitch_jump'] = False
                    if event.key == pygame.K_f:
                        self.button_conditions['screenshot'] = False
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                        
            offset_x = (self.main_surf.get_width() - self.main_surf.get_width()) // 2
            offset_y = (self.main_surf.get_height() - self.main_surf.get_height()) // 2

            self.display.blit(self.main_surf, (offset_x, offset_y))

            self.decoration_surf.set_colorkey((0, 0, 0))
            self.display.blit(self.decoration_surf, (offset_x, offset_y))
            
            img = self.font.render(str(int(self.clock.get_fps())), True, (255, 255, 255))
            self.ui_surf.blit(img, (930, 10))
        
            for name, obj in self.ui.items():
                state = 'pressed' if (name in self.button_conditions and self.button_conditions[name]) else mpos
                obj.render(self.ui_surf, state)
            
            for name, obj in self.player.buffs.items():
                obj.ui.render(self.ui_surf, list(self.player.buffs).index(name))
                if obj.ui.end:
                    self.player.buffs = {}
                    break
            
            screen_surface = pygame.transform.scale(self.display, self.screen.get_size())
            
            
            if self.screenshot_effect:
                current_time = pygame.time.get_ticks()
                elapsed_time = current_time - self.effect_start_time
                
                if elapsed_time < self.effect_duration:
                    
                    progress = elapsed_time / self.effect_duration 
                    flash_alpha = int(255 * (1 - progress) ** 2) 

                    flash_surface = pygame.Surface(self.screen.get_size())
                    flash_surface.fill((255, 255, 255))  
                    flash_surface.set_alpha(flash_alpha)
                    self.ui_surf.blit(flash_surface, (0, 0)) 
                else:
                    self.screenshot_effect = False
            
            if self.transition:
                
                transition_surf = pygame.Surface(self.ui_surf.get_size())
                transition_surf.fill((1,0,0))
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.ui_surf.get_width() // 2, self.ui_surf.get_height() // 2), (30 - abs(self.transition)) * 15)
                transition_surf.set_colorkey((255, 255, 255))
                self.ui_surf.blit(transition_surf, (0, 0))
                
                self.transition -= self.transition_speed
                if self.transition <= 0:
                    self.transition = 0
            
            self.main_shader.render(screen_surface, self.ui_surf, self.t,
                                    self.noise_cof)
            
            pygame.display.flip()
            self.clock.tick(60)
            
if __name__ == "__main__":
    Game().run()