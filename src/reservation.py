class Reservation(object):
    def __init__(self):
        self.valid = True
        self.timer = 0
        self.ready = False    
    
    def make_ready(self):
        self.ready = True
        self.timer = 2500

    def release(self):
        self.valid = False
        
    def update(self):
        if self.ready:
            self.timer -= 1
            if self.timer <= 0:
                self.timer = 0
                self.valid = False