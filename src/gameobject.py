"""
This modules provides a base class for game objects
"""

from vector import Vec2d

class GameObject(object):

    def __init__(self, game):
        """Initialize with the given game."""
        self._game = game
        self._pos = (0,0)
        self.id = game.make_object_id()
        self._selected= False        
        self._render_state = { "selected": self._selected}

    def _set_pos(self, pos):
        self._pos = Vec2d(pos)
        
    def _get_pos(self):
        return self._pos
        
    position = property( _get_pos, _set_pos, 
                doc="""Position of the object""")
    
    def update(self):
        """Perform a single logic frame."""
        pass
        
    def set_selected(self, sel): 
        """Sets the selected status to the given value.
        
        Sets the selected status to the given value. 
        Calls on_select or on_deselect when appropriate.
        """
        old_sel = self._selected
        self._selected = sel        
        
        if ( old_sel == False and sel == True):
            self.on_select()
        elif ( old_sel == True and sel == False):
            self.on_deselect()
        
    def on_select(self):
        """Handles selection events."""
        pass
        
    def on_deselect(self):
        """Handles deselection events."""
        pass
        
    def get_render_state(self):
        """Constructs and returns the render state for this object."""
        pass
        