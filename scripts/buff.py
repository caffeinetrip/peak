
from scripts.ui import BuffUI

class Buff():
    def __init__(self, name, duration, effect, entity, image):
        
        self.name = name
        self.duration = duration
        self.effect = effect
        
        self.entity = entity
        
        self.ui = BuffUI(name, image, duration, 50, 50)

    def activate_effect(self):
        self.effect(self)

def x2jump(self):
    pass
