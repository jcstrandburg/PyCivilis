import pygame, math
from collections import deque

import vector
import game

LEFTCLICK = 1
RIGHTCLICK = 2

class Game(object):
    """Class that provides generic game management functionality."""

    def __init__(self):
        self._next_id = 0
        self._objects = []
        self.selected_obj = None
            
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

    def select(self, object):
        self.selected_obj = object
        
    def deselect(self, object):
        if self.selected_obj == object:
            self.selected_obj = None
            
class GameObject(object):
    """Base class for all objects that exist within the game simulation."""

    def __init__(self, game, size=(100,100), position=(0,0)):
        """Initialize with the given game."""
        self.finished = False
        self.rect = pygame.Rect(0,0,size[0],size[1])
        self.rect.center = position
        self._position = vector.Vec2d( position)
        self.game = game
        self._selected = False
        self.id = game.new_object_id()
        self._render_state = { "selected": self._selected}
        self.selectable = False
        self.target_actions = set([])
        self.abilities = set([])

    def _set_pos(self, pos):
        self.rect.center = self._position = vector.Vec2d(pos)
        
    def _get_pos(self):
        return self._position
        
    position = property( _get_pos, _set_pos, 
                doc="""Center position of the object""")
                
    def select(self):
        self.game.select( self)
        self._selected = True
        
    def deselect(self):
        self.game.deselect( self)
        self._selected = False

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

class Workspace(GameObject):

    def __init__(self, game, pos):
        GameObject.__init__(self, game, (50,50), pos)
        self.reserved = False
        
    def reserve(self):
        self.reserved = True
        
    def release(self):
        print "released"
        self.reserved = False
        
class WorkspaceReservation(object):
    def __init__(self):
        self.valid = True
        self.timer = 0
        self.workspace = None
        self.ready = False
        
    def make_ready(self, workspace):
        self.ready = True
        self.timer = 25
        self.workspace = workspace

    def release(self):
        if self.workspace is not None:
            self.workspace.release()
        self.valid = False
        
    def update(self):
        if self.ready:
            self.timer -= 1
            if self.timer <= 0:
                self.timer = 0
                self.valid = False

class ResourceStorage(object):
    def __init__(self, capacity, accept_list):
        self.accepts = tuple(accept_list)
        self.capacity = capacity
        self.contents = {}
        for tag in self.accepts:
            self.contents[tag] = 0
            
    def deposit(self, tag, amount=1):
        try:
            self.contents[tag] += amount
        except KeyError:
            self.contents[tag] = amount
            
    def get_capacity(self, tag):
        if tag is None or tag in self.accepts:
            return self.get_capacity(None)
        else:
            return 0

    def get_contents(self, tag=None):
        if tag is None:
            return self.contents
        else:
            try:
                return self.contents[tag]
            except KeyError:
                return 0
            
    def withdraw(self, tag, amount):
        try:
            self.contents[tag] -= amount
        except KeyError:
            return 0
            
        
                
class StructureObject(GameObject):

    def __init__(self, game, size=(100,100), position=(0,0), num_workspaces=1):
        GameObject.__init__(self,game,size,position)
        self.workspaces = []
        self.reservations = []
        self.res_storage = ResourceStorage(10, ('stone', 'wood'))
        
        rad = math.pi/4.0
        arc = (num_workspaces-1)*rad
        dist = 100
        basepos = position
        
        for i in range(num_workspaces):
            angle = rad*i - arc/2.0
            pos = vector.Vec2d(dist*math.sin(angle), dist*math.cos(angle)) + basepos
            workspace = Workspace(game, pos)
            self.workspaces.append( workspace)
        
    def update(self):
        GameObject.update(self)
        
        #nix invalid reservations
        while len(self.reservations) > 0 and self.reservations[0].valid == False:
            self.reservations.pop(0)
        
        #attempt to fill the first reservation in the list
        if len(self.reservations) > 0:
            res = self.reservations[0]
            for wspace in self.workspaces:
                if not wspace.reserved:
                    print "ready"
                    res.make_ready( wspace)
                    self.reservations.pop(0)
                    break
                
        
    def reserve_workspace(self):
        reservation = WorkspaceReservation()
        self.reservations.append( reservation)
        return reservation
    