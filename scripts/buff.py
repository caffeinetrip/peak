
from scripts.ui import BuffUI

class Buff():
    def __init__(self, name, duration, entity, image):
        
        self.name = name
        self.duration = duration
        
        self.entity = entity
        
        self.ui = BuffUI(name, image, duration, 50, 50)
