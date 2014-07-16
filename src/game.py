import pygame

import vector
import game

LEFTCLICK = 1
RIGHTCLICK = 2

class Game(object):
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
    def __init__(self, game):
        """Initialize with the given game."""
        self.finished = False
        self.rect = pygame.Rect(0,0,100,100)
        self._position = vector.Vec2d( self.rect.center)
        self.game = game
        self._selected = False
        self.id = game.new_object_id()
        self._selected= False        
        self._render_state = { "selected": self._selected}

    def _set_pos(self, pos):
        self.rect.center = self._position = pos
        
    def _get_pos(self):
        return self._position
        
    position = property( _get_pos, _set_pos, 
                doc="""Position of the object""")

    def selectable(self):
        """returns whether the object is selectable"""
        return False
                
    def select(self):
        pass
        
    def deselect(self):
        pass

    def get_selected(self):
        return self._selected
        
    def set_selected(self, sel): 
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

    selected = property(get_selected, set_selected)
            
    def on_create():
        pass
        
    def on_destroy():
        pass
        
    def update(self):
        pass
        
    def get_render_state(self):
        return self._render_state