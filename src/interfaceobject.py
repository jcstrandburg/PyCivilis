"""Framework for interface objects."""

class InterfaceObject(object):
    """Base class for all interface objects."""
    
    def __init__(self):
        self.layer = 0
        pass
        
    def mouse_is_over(self, pos):
        """Returns true if the mouse is over this object."""
        pass
        
    def update(self, viewport):
        pass
        
    def draw(self, viewport):
        pass
        
    def select(self):
        pass
    
    def deselect(self):
        pass
        
    def selectable(self):
        return False
        
    def is_selected(self):
        return False
        
    def set_render_state(self, state):
        pass

    def handle_event(self, event):
        """Handles a pygame input event."""
        pass