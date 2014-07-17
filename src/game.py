import pygame

import vector
import game

LEFTCLICK = 1
RIGHTCLICK = 2

class Game(object):
    """Class that provides generic game management functionality."""

    def __init__(self):
        self._next_id = 0
        self._objects = []
            
    def update(self):
        for o in self._objects:
            o.update()

        #remove "finished" objects
        i, j = 0, 0
        while j < len(self._objects):
            if not self._objects[j].finished:
                self._objects[i] = self._objects[j]
                i+=1        
            j += 1        
        del self._objects[i:]        
            
    def add_game_object(self, obj):
        self._objects.append(obj)
        
    def remove_game_object(self, ojb):
        self._objects.remove(obj)
        
    def new_object_id(self):
        self._next_id += 1
        return self._next_id
        
    
class GameObject(object):
    """Base class for all objects that exist within the game simulation."""

    def __init__(self, game, size=(100,100), position=(0,0)):
        """Initialize with the given game."""
        self.finished = False
        self.rect = pygame.Rect(0,0,size[0],size[1])
        self.rect.center = position;
        self._position = vector.Vec2d( position)
        self.game = game
        self._selected = False
        self.id = game.new_object_id()
        self._render_state = { "selected": self._selected}

    def _set_pos(self, pos):
        self.rect.center = self._position = pos
        
    def _get_pos(self):
        return self._position
        
    position = property( _get_pos, _set_pos, 
                doc="""Center position of the object""")

    def selectable(self):
        """returns whether the object is selectable"""
        return False
                
    def select(self):
        pass
        
    def deselect(self):
        pass

    def _get_selected(self):
        return self._selected
        
    def _set_selected(self, sel): 
        """Sets the selected status to the given value.
        
        Sets the selected status to the given value. 
        Calls select or deselect when appropriate.
        """
        old_sel = self._selected
        self._selected = sel        
        
        if ( old_sel == False and sel == True and selectable()):
            self.on_select()
        elif ( old_sel == True and sel == False):
            self.on_deselect()        

    selected = property(_get_selected, _set_selected)
            
    def on_create():
        pass
        
    def on_destroy():
        pass
        
    def update(self):
        pass
        
    def get_render_state(self):
        return self._render_state