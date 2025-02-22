import sys, pygame, random, json
from OpenGL import *
from scripts.utils import Animation, Tileset, load_image
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.ui import SkillsUI
from scripts.buff import *
from scripts.shaders import Shader
from scripts.particles import Particle, load_particle_images

pygame.init()

FONT = pygame.font.SysFont('data/texts/BoutiqueBitmap9x9_1.9.ttf', 24)
class Game():
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption('peak')
        
        self.main_shader = Shader('shader', ['game_shader', 'ui_shader'])
        
        # SET DISPLAY WIDTH, HEIGHT
        self.display = pygame.Surface((384, 216))

        self.displays = {
            'main': self.display.copy(),
            'decoration': self.display.copy(),
            'ui': pygame.Surface((960, 540)),
        }
        
        self.scenes = {
            'current': 'menu',
            'sub_scene': 'menu'
        }
        
        self.button_conditions = {'glitch_dash': False, 'glitch_jump': False, 'screenshot': False}
        
        self.noise = {'cof': 1.0, 'target_cof': 1.0, 'speed': 0.025}
        
        self.clock = pygame.time.Clock()
        self.movement = [False, False]
        
        self.checkpoint = [180, 100]
        
        self.music = {
            "game": 'data/music/nether.mp3',
            "menu": 'data/music/main_menu.mp3',
            "ending": 'data/music/final_death.mp3'
        }
        
        self.sounds = {
            'jump': pygame.mixer.Sound('data/sounds/jump.mp3'),
            'death': pygame.mixer.Sound('data/sounds/death.mp3'),
            'land': pygame.mixer.Sound('data/sounds/land.mp3'),
            'dash': pygame.mixer.Sound('data/sounds/dash.mp3'),
        }
        
        self.animations = {
            'player/idle': Animation('data/assets/Animations/Player/idle/anim1.png', img_dur=30),
            'player/edge_idle': Animation('data/assets/Animations/Player/idle/anim2.png', img_dur=30),
            'player/run': Animation('data/assets/Animations/Player/walk/anim1.png', img_dur=6),
            'player/jump': Animation('data/assets/Animations/Player/jump/anim1.png', img_dur=7, loop=False),
            'player/wall_slide': Animation('data/assets/Animations/Player/slide/anim1.png'),
            'player/fall': Animation('data/assets/Animations/Player/fall/anim1.png'),
            'player/land': Animation('data/assets/Animations/Player/land/anim1.png', img_dur=20, loop=False),
            'player/dash': Animation('data/assets/Animations/Player/dash/anim1.png', img_dur=1, loop=False),
            'player/death': Animation('data/assets/Animations/Player/death/anim1.png', img_dur=3, loop=False),
            'danger_block/create': Animation('data/assets/map_tiles/test_map/anim1.png', img_dur=7, loop=False),
        }
        
        self.player = Player(self, (50, 50), (8, 15))
        self.death_count = 0
        self.particles = []
        
        self.map = {
            'name': 'map',
            'tileset': Tileset("data/assets/map_tiles/test_map/tileset.png", 16).load_tileset(),
            'tilemap': Tilemap(tile_size=16),
            'rotatesset': {} 
        }
        
        self.death_vfx_timer = 0
        
        self.screenshot_vfx = {
            'enabled': False,
            'duration': 2000,
            'alpha': 250,
            'start_time': 0
        }
        
        self.transition_vfx = {
            'value': 0,
            'speed': 1,
        }
        
        self.anomaly_text_vfx = {
            'enabled': False,
            'alpha': 0,
            'timer': 0,
            'duration': 2000,
        }
        
        load_particle_images('data/assets/particles')
        self.load_level(self.map['name'])
        self.t = 0
        
        self.anomaly_near = False

        self.load_data()

    # FUNCTIONS
    def load_level(self, level_name):
        self.map['tilemap'].load('data/levels/' + level_name + '.json')
        self.map['rotateset'] = {}

        self.anomaly_positions = [
            (355, 177),
            [2299, -719],
            [1069, -607],
            [1266, -687],
        ]

        self.ui = {
            'glitch_dash': SkillsUI(50,50, load_image('data/assets/spells/glitch_dash.png'), 400, 475, 3 , 'Q'),
            'glitch_jump': SkillsUI(50,50, load_image('data/assets/spells/glitch_jump.png'), 460, 475, 3, 'E'),
            'screenshot': SkillsUI(50,50, load_image('data/assets/spells/screenshot.png'), 520, 475, 8, 'F'),
        }

        self.player.death = False
        self.player = Player(self, self.checkpoint, (8, 15)) 
        self.transition_vfx['value'] = 30 
        self.death_vfx_timer = 0 
        
        self.scroll = [0, 0]
        self.render_scroll = [0,0]

    def save_data(self):
        data = {
            'player_pos': list(self.player.pos),
            'checkpoint': list(self.checkpoint),
            'death_count': self.death_count,
            'tilemap': self.map['tilemap'].tilemap,
            'level': self.map['name'],
            'rotate_tiles': self.map['rotateset'],
            'scroll': self.scroll
        }
        
        with open("data/saves/save.json", "w") as outfile:
            json.dump(data, outfile, indent=4)
        
    def load_data(self):
        save_file = "data/saves/save.json"
        
        if os.path.exists(save_file):
            try:
                with open(save_file, "r") as infile:
                    data = json.load(infile)
                    
                    self.checkpoint = data.get('checkpoint', self.checkpoint)
                    self.death_count = data.get('death_count', self.death_count)
                    self.map['name'] = data.get('level', self.map['name'])
                    
                    self.load_level(self.map['name'])
                    
                    self.map['tilemap'].tilemap = data.get('tilemap', self.map['tilemap'].tilemap)
                    self.map['rotateset'] = data.get('rotate_tiles', self.map['rotateset'])
                    self.scroll = data.get('scroll', self.scroll)
                    self.player.pos = data.get('player_pos', self.player.pos)
                    
            except json.JSONDecodeError:
                print("Warning: save.json is corrupted or empty. Initializing with default values.")

    def is_anomaly_near(self):
        for pos in self.anomaly_positions:
            if pos[0]-self.scroll[0] < self.display.get_width() and pos[1]-self.scroll[1] < self.display.get_height():
                if  pos[0]-self.scroll[0] > 0 and pos[1]-self.scroll[1] > 0:
                    return pos
        return False

    def play_music(self, music_file, loops=-1, fade_ms=0):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(loops, fade_ms=fade_ms)

    def stop_music(self, fade_ms=0):
        pygame.mixer.music.fadeout(fade_ms)

    # GAME
    def game(self):
        
        self.play_music(self.music['game'], fade_ms=2000)

        while self.scenes['current'] == 'game':
            self.t += self.clock.get_time() / 1000

            #  NOISE
            self.anomaly_near = self.is_anomaly_near()
            
            if self.anomaly_near:
                self.noise['target_cof'] = 1.5
                
                if self.anomaly_near == [2299, -719]:
                    self.noise['target_cof'] = 3
                 
            else:
                self.noise['target_cof'] = 1.0 
                
            self.noise['cof'] += (self.noise['target_cof'] - self.noise['cof']) * self.noise['speed']
            
            
            # DISPLAYS
            self.displays['ui'].fill((0,0,0))
            self.displays['main'].fill((0, 0, 0))
            self.displays['decoration'].fill((0, 0, 0))
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 25
            self.scroll[1] += ((self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1])-25) / 25
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            self.map['tilemap'].render(
                self.displays['main'],
                self.displays['decoration'],
                self.map['tileset'],
                self.map['rotatesset'],
                offset=self.render_scroll
            )
            
            tilemap_surf = self.displays['main'].copy().convert_alpha()
            tilemap_surf.set_colorkey((0,0,0))
            
            # PARTICLES
            if 0 <= self.player.pos[0] - self.scroll[0] < self.displays['main'].get_width() and 0 <= self.player.pos[1] - self.scroll[1] + 1 < self.displays['main'].get_height():
                if self.player.action == 'run':
                    for i in range(random.randint(1,3)):
                        if random.randint(1,20) == 1:
                            
                            if random.randint(1,10) == 5:
                                particle_color = (51,51,51)
                            elif random.randint(1,25) == 5:
                                particle_color = (140,140,140)
                            else:
                                particle_color = self.displays['main'].get_at((self.player.pos[0] + self.player.size[0] - self.scroll[0], self.player.pos[1] + self.player.size[1] - self.scroll[1] + 1))
                            
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
                    
                    for i in range(random.randint(1,2)):
                        if i == 1:
                            if random.randint(1,10) == 5:
                                particle_color = (51,51,51)
                            else:
                                x = self.player.pos[0] + self.player.size[0] - self.scroll[0]
                                y = self.player.pos[1] + self.player.size[1] - self.scroll[1] + 1
                                width, height = self.displays['main'].get_size()
                                if 0 <= x < width and 0 <= y < height:
                                    particle_color = self.displays['main'].get_at((x, y))
                                else:
                                    particle_color = (0, 0, 0, 0) 
                            
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
                                (150,150,150),
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
                        
            for particle in self.particles[:]:
                particle.update(self.clock.get_time() / 45)
                
            for particle in self.particles:
                particle.draw(self.displays['main'], self.scroll)
                
            self.displays['main'].blit(tilemap_surf)

            # PLAYER
            self.player.update(self.map['tilemap'], (self.movement[1] - self.movement[0], 0))
            self.player.render(self.displays['main'], offset=self.render_scroll)
            
            # EVENTS
            for event in pygame.event.get():
                    
                if event.type == pygame.QUIT:
                    self.scenes['sub_scene'] = 'exit'
                    self.transition_vfx['value'] = 30
                        
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_a:
                        self.movement[0] = True
                        
                    if event.key == pygame.K_0:
                        self.map['tilemap'].load('data/levels/' + self.map['name'] + '.json')
                        
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                        
                    if event.key == pygame.K_w and self.player.velocity[1] != 0.321321:
                        
                        if 'x2jump' in self.player.buffs:
                            self.player.jump(-1.15)
                        else:
                            self.player.jump()
                        
                    if event.key == pygame.K_q and self.ui['glitch_dash'].active:
                        self.button_conditions['glitch_dash'] = True
                        self.player.dash()
                        self.ui['glitch_dash'].active = False
                        
                    if event.key == pygame.K_e and self.ui['glitch_jump'].active:
                        self.button_conditions['glitch_jump'] = True
                        self.player.buffs['x2jump'] = Buff('x2jump', 1.5, self.player, load_image('data/assets/spells/glitch_jump.png'))
                        self.ui['glitch_jump'].active = False
                            
                    if event.key == pygame.K_f and self.ui['screenshot'].active:
                        self.button_conditions['screenshot'] = True
                        self.ui['screenshot'].active = False
                        self.screenshot_vfx['enabled'] = True
                        self.screenshot_vfx['start_time'] = pygame.time.get_ticks()

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
            
            # GAME RENDER   
            offset_x = (self.displays['main'].get_width() - self.displays['main'].get_width()) // 2
            offset_y = (self.displays['main'].get_height() - self.displays['main'].get_height()) // 2

            self.display.blit(self.displays['main'], (offset_x, offset_y))

            self.displays['decoration'].set_colorkey((0, 0, 0))
            self.display.blit(self.displays['decoration'], (offset_x, offset_y))
            
            screen_surface = pygame.transform.scale(self.display, self.screen.get_size())
            
            # UI RENDER
            img = FONT.render(str(int(self.clock.get_fps())), True, (255, 255, 255))
            self.displays['ui'].blit(img, (930, 10))
        
            for name, obj in self.ui.items():
                state = 'pressed' if (name in self.button_conditions and self.button_conditions[name]) else None
                obj.render(self.displays['ui'], state)
            
            for name, obj in self.player.buffs.items():
                obj.ui.render(self.displays['ui'], list(self.player.buffs).index(name))
                if obj.ui.end:
                    self.player.buffs = {}
                    break

            if self.anomaly_text_vfx['enabled']:
                    if self.anomaly_text_vfx['timer'] == 0:
                        self.anomaly_text_vfx['timer'] = pygame.time.get_ticks()
                    
                    elapsed_time = pygame.time.get_ticks() - self.anomaly_text_vfx['timer']
                    
                    if elapsed_time < self.anomaly_text_vfx['duration']:
                        if elapsed_time < self.anomaly_text_vfx['duration'] / 2:
                            self.anomaly_text_vfx['alpha'] = min(255, self.anomaly_text_vfx['alpha'] + 10)
                        else:
                            self.anomaly_text_vfx['alpha'] = max(0, self.anomaly_text_vfx['alpha'] - 10)
                            
                        if self.anomaly_near:
                            text_surface = FONT.render("Anomaly is near you!!!", True, (252, 3, 3))
                            
                        else:
                            text_surface = FONT.render("Anomaly not founded", True, (255, 255, 255))
                            
                        text_surface.set_alpha(self.anomaly_text_vfx['alpha'])
                        
                        text_rect = text_surface.get_rect(center=(self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2 + 150))
                        self.displays['ui'].blit(text_surface, text_rect)
                        
                    else:
                        self.anomaly_text_vfx['timer'] = 0
                        self.anomaly_text_vfx['alpha'] = 0
                        self.anomaly_text_vfx['enabled'] = False
                    
            
            if self.screenshot_vfx['enabled']:
                current_time = pygame.time.get_ticks()
                elapsed_time = current_time - self.screenshot_vfx['start_time']
                
                if elapsed_time < self.screenshot_vfx['duration']:
                    
                    self.displays['ui'].fill((1,0,0))
                    
                    progress = elapsed_time / self.screenshot_vfx['duration'] 
                
                    self.screenshot_vfx['alpha'] = int(255 * (1 - progress) ** 2) 
                    
                    flash_surface = pygame.Surface(self.screen.get_size())
                    flash_surface.fill((255, 255, 255))  
                    flash_surface.set_alpha(self.screenshot_vfx['alpha'])
                    self.displays['ui'].blit(flash_surface, (0, 0)) 
                    
                    if self.screenshot_vfx['alpha'] < 10:
                        self.transition_vfx['value'] = 30
                    
                else:
                    self.screenshot_vfx['enabled'] = False
                    self.screenshot_vfx['alpha'] = 250
                    self.anomaly_text_vfx['enabled'] = True
                    
                    if self.anomaly_near:
                        self.player.left_channel_bust.play(self.player.sounds['anomaly_1'])
                    else:
                        self.player.left_channel_bust.play(self.player.sounds['anomaly_0'])
                        
            if self.transition_vfx['value']:
                transition_surf = pygame.Surface(self.displays['ui'].get_size())
                transition_surf.fill((1,0,0))
                
                if self.transition_vfx['value'] > 0:
                    if self.player.death or self.screenshot_vfx['alpha'] < 10 or self.scenes['sub_scene'] == 'exit':
                        pygame.draw.circle(
                            transition_surf, 
                            (255, 255, 255), 
                            (self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2), 
                            max(0, 435 - ((-30+self.transition_vfx['value'])*-1) * 15) // (25 if self.scenes['sub_scene'] == 'exit' else 1)
                        )

                        transition_surf.set_colorkey((255, 255, 255))
                        self.displays['ui'].blit(transition_surf, (0, 0))
                        
                        self.transition_vfx['value'] -= self.transition_vfx['speed'] * 2
                        
                        if self.transition_vfx['value'] <= 0:
                            self.transition_vfx['value'] = 0
                            self.death_vfx_timer = pygame.time.get_ticks()

                            if self.scenes['sub_scene'] == 'exit':
                                self.scenes['current'] = self.scenes['sub_scene']
                                self.stop_music(fade_ms=2000)
                                self.save_data()
                                break 

                    else:
                        pygame.draw.circle(transition_surf, (255, 255, 255), (self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2), (30 - abs(self.transition_vfx['value'])) * 15)
                        transition_surf.set_colorkey((255, 255, 255))
                        self.displays['ui'].blit(transition_surf, (0, 0))
                        
                        self.transition_vfx['value'] -= self.transition_vfx['speed']
                        if self.transition_vfx['value'] <= 0:
                            self.transition_vfx['value'] = 0
                        
           
            elif self.player.death:
                if self.death_vfx_timer > 0:
                    current_time = pygame.time.get_ticks()
                    self.displays['ui'].fill((1, 0, 0)) 
                    if current_time - self.death_vfx_timer >= 250:
                        self.load_level(self.map['name'])
                        self.death_count += 1
                        self.scroll[0] = (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) 
                        self.scroll[1] = ((self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1])-25) 
                        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            
            # UPDATE
            self.main_shader.render(self.t, screen_surface, self.displays['ui'], self.noise['cof'])
                                     
            pygame.display.flip()
            self.clock.tick(60)

    # MAIN MENU
    def menu(self):
        self.scenes['sub_scene'] = 'menu'

        start_font = pygame.font.Font('data/texts/font_7x7.ttf', 24)
        start_text = start_font.render('Play', True, (255, 255, 255))
        start_rect = start_text.get_rect(center=(self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2 + 50))
        
        self.play_music(self.music['menu'], fade_ms=2000)
        
        while self.scenes['current'] == 'menu':
                        
            self.t += self.clock.get_time() / 1000
            self.displays['ui'].blit(load_image('data/background/menu.png'))
            
            # Check if the mouse is hovering over the text
            mpos = pygame.mouse.get_pos()
            scale_x = self.displays['ui'].get_width() / self.screen.get_width()
            scale_y = self.displays['ui'].get_height() / self.screen.get_height()
            mpos_display = (int(mpos[0] * scale_x), int(mpos[1] * scale_y))
            
            hover = start_rect.collidepoint(mpos_display)
            
            if hover:
                scaled_text = pygame.transform.scale(start_text, (int(start_text.get_width() * 1.2), int(start_text.get_height() * 1.2)))
                scaled_rect = scaled_text.get_rect(center=start_rect.center)
                self.displays['ui'].blit(scaled_text, scaled_rect)
            else:
                self.displays['ui'].blit(start_text, start_rect)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.scenes['sub_scene'] = 'exit'
                    self.transition_vfx['value'] = 30
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.scenes['sub_scene'] = 'game'  
                        self.transition_vfx['value'] = 30
                        self.stop_music(fade_ms=2000)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_rect.collidepoint(mpos_display):
                        self.scenes['sub_scene'] = 'game'
                        self.transition_vfx['value'] = 30
                        self.stop_music(fade_ms=2000)
            
            if self.transition_vfx['value']:
                transition_surf = pygame.Surface(self.displays['ui'].get_size())
                transition_surf.fill((10,10,10))
                
                if self.scenes['sub_scene'] == 'exit' or self.scenes['sub_scene'] == 'game':
                    pygame.draw.circle(
                        transition_surf, 
                        (255, 255, 255), 
                        (self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2), 
                        max(0, 435 - ((-30+self.transition_vfx['value'])*-1) * 15) // (25 if self.scenes['sub_scene'] == 'exit' else 1)
                    )
                    transition_surf.set_colorkey((255, 255, 255))
                    self.displays['ui'].blit(transition_surf, (0, 0))
                    
                    self.transition_vfx['value'] -= self.transition_vfx['speed']
                    
                    if self.transition_vfx['value'] <= 0:
                        self.transition_vfx['value'] = 0
                        self.death_vfx_timer = pygame.time.get_ticks()
                        
                        self.scenes['current'] = self.scenes['sub_scene']
                        break  
                
                else:
                    pygame.draw.circle(transition_surf, (255, 255, 255), (self.displays['ui'].get_width() // 2, self.displays['ui'].get_height() // 2), (30 - abs(self.transition_vfx['value'])) * 15)
                    transition_surf.set_colorkey((255, 255, 255))
                    self.displays['ui'].blit(transition_surf, (0, 0))
                    
                    self.transition_vfx['value'] -= self.transition_vfx['speed'] * 2
                    if self.transition_vfx['value'] <= 0:
                        self.transition_vfx['value'] = 0
                    
            self.main_shader.render(self.t, self.displays['ui'])
            
            pygame.display.flip()
            self.clock.tick(60)
            
    # INTRO
    def prolog(self):
        while True:
            pass
    
    # OUTRO
    def ending(self):
        while True:
            pass

# SCENES CONTROLL
if __name__ == "__main__":
    game = Game()

    while True:
        
        game.transition_vfx['value'] = 30
        
        if game.scenes['current'] == 'game':
            game.game()

        elif game.scenes['current'] == 'menu':
            game.menu()
            
        elif game.scenes['current'] == 'prologue':
            game.prolog()

        elif game.scenes['current'] == 'ending':
            game.ending()
            
        elif game.scenes['current'] == 'exit':
            sys.exit()
            break
