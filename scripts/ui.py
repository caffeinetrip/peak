import pygame

class UI():
    def __init__(self, width, height, x, y):
        self.width = width
        self.height = height
    
        self.x = x
        self.y = y
        
        self.original_width = width
        self.original_height = height
        
        self.original_x = x
        self.original_y = y
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.font = pygame.font.Font("data/texts/LuckiestGuy-Regular.ttf", 12)

class SkillsUI(UI):
    def __init__(self, width, height, img, x, y, kd, key):
        super().__init__(width, height, x, y)
        
        self.img = img
        self.form = True
        self.kd = kd
        self.hover = False
        self.key = key
        
        self.kd_time = 0
        self.hover_end_time = 0 
        self.active = True

    def render(self, surf, mpos):
        current_time = pygame.time.get_ticks()
        
        if mpos == 'pressed' or self.rect.collidepoint(mpos):
            self.hover = True
            self.hover_end_time = current_time + 40
        elif current_time < self.hover_end_time:
            self.hover = True
        else:
            self.hover = False

        if self.hover:
            self.width = int(self.original_width * 1.2)
            self.height = int(self.original_height * 1.2)
            self.x = self.original_x - (self.width - self.original_width) // 2
            self.y = self.original_y - (self.height - self.original_height) // 2
        else:
            self.width = self.original_width
            self.height = self.original_height
            self.x = self.original_x
            self.y = self.original_y

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        scaled_img = pygame.transform.scale(self.img, (self.width, self.height))
            
        surf.blit(scaled_img, (self.x, self.y))

        key_text = self.font.render(self.key, True, (0, 0, 1))
        key_width, key_height = key_text.get_size()
        square_size = max(key_width, key_height) + 4

        square_x = self.x - 1
        square_y = self.y - 1

        text_x = square_x + (square_size - key_width) // 2
        text_y = square_y + (square_size - key_height) // 2
        
        if not self.active:
            current_time = pygame.time.get_ticks()

            if self.kd_time == 0:
                self.kd_time = current_time

            elapsed_time = current_time - self.kd_time
            cooldown_progress = elapsed_time / (self.kd * 1000)

            if cooldown_progress >= 1:
                self.active = True
                self.kd_time = 0
            else:
                overlay_height = int((self.height - 10) * (1 - cooldown_progress))
                overlay_surface = pygame.Surface((scaled_img.get_width() - 7, overlay_height), pygame.SRCALPHA)
                overlay_surface.fill((0, 0, 0, 128))

                surf.blit(overlay_surface, (self.x + 4, self.y + self.height - overlay_height - 5))
        
        pygame.draw.rect(surf, (255, 255, 255), (square_x - 1, square_y - 1, square_size, square_size))
        pygame.draw.rect(surf, (0, 0, 1), (square_x - 1, square_y - 1, square_size, square_size), 2)

        surf.blit(key_text, (text_x, text_y))

class BuffUI(UI):
    def __init__(self, name, img, duration, width, height):
        super().__init__(width, height, 0, 0)
        
        self.img = img
        self.duration = duration
        self.add_time = pygame.time.get_ticks()
        
        self.active = True
        self.kd_time = 0
        
        self.name = name
        
        self.create_duration = 0.3  # Duration of the appear animation
        self.dissapear_duration = 0.25  # Duration of the disappear animation

        self.target_x = 0
        self.move_speed = 0.1
        self.move_speed_2 = 0.5
        
        self.end = False
        self.clearing = False  # New flag to indicate the buff is being cleared
        
        self.font = pygame.font.Font("data/texts/LuckiestGuy-Regular.ttf", 9)

    def render(self, surf, index):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if index > 0:
            self.target_x = index * self.width
            self.x += (self.target_x - self.x) * self.move_speed_2
        else:
            self.target_x = index * self.width
            self.x += (self.target_x - self.x) * self.move_speed

        if self.active or self.clearing:  # Allow rendering during the clearing animation
            current_time = pygame.time.get_ticks()

            if self.kd_time == 0:
                self.kd_time = current_time

            elapsed_time = current_time - self.kd_time
            cooldown_progress = elapsed_time / (self.duration * 1000)
            
            remaining_time = max(0, (self.kd_time + self.duration * 1000 - current_time) / 1000)
            key_text = self.font.render(str(int(remaining_time)), True, (0, 0, 1))
            key_width, key_height = key_text.get_size()
            square_size = max(key_width, key_height) + 4

            kd_counter_surf = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
            pygame.draw.rect(kd_counter_surf, (255, 255, 255), (0, 0, square_size, square_size))
            pygame.draw.rect(kd_counter_surf, (0, 0, 1), (0, 0, square_size, square_size), 2)
            kd_counter_surf.blit(key_text, ((square_size - key_width) // 2, ((square_size - key_height) // 2)+1))

            if cooldown_progress >= 1 and not self.clearing:
                self.active = False
                self.kd_time = 0

            if current_time <= (self.add_time + self.create_duration * 1000):

                elapsed_time = current_time - self.add_time
                cooldown_progress = elapsed_time / (self.create_duration * 1000)

                scaled_img = pygame.transform.scale(
                    self.img, 
                    (int(self.width * cooldown_progress), int(self.height * cooldown_progress))
                )
                
                kd_counter_surf = pygame.transform.scale(
                    kd_counter_surf, 
                    (int(kd_counter_surf.get_width() * cooldown_progress), int(kd_counter_surf.get_height() * cooldown_progress))
                )

                surf.blit(scaled_img, (self.x + (25 - 25 * cooldown_progress), self.y + (25 - 25 * cooldown_progress)))
                surf.blit(kd_counter_surf, ((self.x - square_size + 15), (self.y - square_size + 15)))

            elif self.clearing or current_time >= (self.add_time + (self.duration * 1000 - self.dissapear_duration * 1000)):

                if not self.clearing:
                    self.clearing = True
                    self.clear_start_time = current_time 

                elapsed_time = current_time - self.clear_start_time
                cooldown_progress = 1 - (elapsed_time / (self.dissapear_duration * 1000))

                if cooldown_progress > 0:
                    scaled_img = pygame.transform.scale(
                        self.img, 
                        (int(self.width * cooldown_progress), int(self.height * cooldown_progress))
                    )
                    
                    surf.blit(scaled_img, (self.x + (25 - 25 * cooldown_progress), self.y + (25 - 25 * cooldown_progress)))
                
                else:
                    self.end = True  
                
            else:
                scaled_img = pygame.transform.scale(self.img, (self.width, self.height))
                surf.blit(scaled_img, (self.x, self.y))
                
                surf.blit(kd_counter_surf, (self.x - square_size + 15, self.y - square_size + 15))
            
        else:
            return self.name

    def clear_buff(self):

        if not self.clearing:
            self.clearing = True
            self.clear_start_time = pygame.time.get_ticks()