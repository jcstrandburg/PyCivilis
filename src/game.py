import pygame, math
from collections import deque

import vector

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
        
    def remove_game_object(self, obj):
        self._objects.remove(obj)
        
    def new_object_id(self):
        self._next_id += 1
        return self._next_id

    def select(self, object):
        self.selected_obj = object
        
    def deselect(self, object):
        if self.selected_obj == object:
            self.selected_obj = None
            
    """Game specific code"""
    
    def reserve_storage(self, position, carrying):
        candidates = []
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "get_available_space"):
                if obj.get_available_space(carrying['type']) >= carrying['qty']:
                    candidates.append( obj)

        candidates.sort(key=lambda candidate: (candidate.position-position).get_length())
                    
        if ( len(candidates) > 0):
            return candidates[0].reserve_storage(carrying['type'], carrying['qty'])
        return None

    
    def find_reservoir(self, position, resource_type, qty=1):
        candidates = []
        backups = []
        print "Attempting to find reservoir for "+str(resource_type)+"in qty "+str(qty)
        
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "res_reservoir") and obj.res_reservoir is not None:
                avail = obj.res_reservoir.get_available_contents(resource_type)
                if avail >= qty:
                    candidates.append( obj)
                elif avail > 0 or obj.res_reservoir.regen_rate > 0:
                    backups.append( obj)

        candidates.sort(key=lambda candidate: (candidate.position-position).get_length())
                    
        if ( len(candidates) > 0):
            return candidates[0]
        
        backups.sort(key=lambda candidate: (candidate.position-position).get_length())
        
        if ( len(backups) > 0):
            return backups[0]        
        
        return None

            
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
        
        if ( old_sel == False and sel == True and self.selectable()):
            self.on_select()
        elif ( old_sel == True and sel == False):
            self.on_deselect()        

    selected = property(_get_selected, _set_selected)
            
    def on_create(self):
        pass
        
    def on_destroy(self):
        pass
        
    def update(self):
        pass
        
    def get_render_state(self):
        return self._render_state

class Workspace(GameObject):

    def __init__(self, game, structure, pos):
        GameObject.__init__(self, game, (50,50), pos)
        self.reserved = False
        self.struct = structure
        
    def reserve(self):
        self.reserved = True
        
    def release(self):
        self.reserved = False
        
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
        
class WorkspaceReservation(Reservation):
    def __init__(self):
        Reservation.__init__(self)
        self.workspace = None
        
    def make_ready(self, workspace):
        Reservation.make_ready(self)
        self.workspace = workspace

    def release(self):
        Reservation.release(self)
        if self.workspace is not None:
            self.workspace.release()

class ResourceReservation(Reservation):
    def __init__(self, structure):
        Reservation.__init__(self)
        self.structure = structure
        
    def make_ready(self):
        Reservation.make_ready(self)


class ResourceReservoir(object):
    def __init__(self, structure, qty, res_type, regen_rate=0):
        self.structure = structure
        self.resource_type = res_type
        self.capacity = qty
        self.quantity = qty
        self.reservations = []
        self.regen_rate = regen_rate
        self.debug_string = 'debug'
        
    def reserve(self, tag=None, amount=1):
        if tag is None:
            tag = self.resource_type
            
        qty = self.get_available_contents(tag)
        res = ResourceReservation(self.structure)
        self.reservations.append(res)
        
        if qty >= amount:
            res.make_ready()
            
        return res
       
        
    def update(self):
        for r in self.reservations:
            r.update()
        self.reservations[:] = [r for r in self.reservations if r.valid]
        
        self.quantity += self.regen_rate
        self.quantity = min( self.quantity, self.capacity)
        
        pending_res = [r for r in self.reservations if not r.ready]
        count = min(len(pending_res), int(self.get_available_contents(self.resource_type)+len(pending_res)))
        for i in xrange(count):
            pending_res[i].make_ready()
            
        self.debug_string = str(len(self.reservations)) +":" + str(len(pending_res))

    def get_contents(self, tag):
        if self.resource_type == tag:
            return self.quantity
        else:
            return 0
        
    def get_available_contents(self, tag):
        if self.resource_type == tag:
            return self.quantity - len(self.reservations)
        else:
            return 0
        
    def withdraw(self, res_type, qty):
        if self.resource_type == res_type:
            qty = min(qty, self.quantity)
            if qty > 0:
                self.quantity -= qty
                return {'type':res_type, 'qty': qty}            
            else:
                return None
        else:
            return None
        
class ResourceStorage(object):
    def __init__(self, structure, capacity, accept_list):
        self.structure = structure
        self.accepts = tuple(accept_list)
        self.capacity = capacity
        self.contents = {}
        self.reservations = []
        for tag in self.accepts:
            self.contents[tag] = 0

    def do_decay(self):
        for key in self.contents:
            self.contents[key] = max(0, self.contents[key]-0.001)

    def reserve(self, tag, amount=1):
        cap = self.get_available_space(tag)
        if cap >= amount:
            res = ResourceReservation(self.structure)
            res.make_ready()
            self.reservations.append(res)
            return res
        else:
            return None
            
    def deposit(self, resource):
        if self.get_available_space(resource['type']) < resource['qty']:
            return False
                    
        try:
            self.contents[resource['type']] += resource['qty']
        except KeyError:
            if resource['type'] in self.accepts:
                self.contents[resource['type']] = resource['qty']
                
        return True
            
    def get_available_space(self, tag):
        if tag is None or tag in self.accepts:
            cap = self.capacity
            for key in self.contents:
                cap -= self.contents[key]
            for r in self.reservations:
                if r.valid:
                    cap -= 1
            return cap
        else:
            return 0

    def get_contents(self, tag=None):
        if tag is None:
            content = 0
            for key in self.contents:
                content += self.contents[key]
            return content
        else:
            try:
                return self.contents[tag]
            except KeyError:
                return 0
            
    def update(self):
        for r in self.reservations:
            r.update()

        self.reservations[:] = [r for r in self.reservations if r.valid]           
            
            
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
        self.ready_reservations = []
        self.res_storage = None
        self.res_reservoir = None
        
        rad = math.pi/4.0
        arc = (num_workspaces-1)*rad
        dist = 100
        basepos = position
        
        for i in range(num_workspaces):
            angle = rad*i - arc/2.0
            pos = vector.Vec2d(dist*math.sin(angle), dist*math.cos(angle)) + basepos
            workspace = Workspace(game, self, pos)
            self.workspaces.append( workspace)
            
    def set_storage(self, cap, accepts):
        self.res_storage = ResourceStorage(self, cap, accepts)

    def set_reservoir(self, qty, res_type, regen_rate):
        self.res_reservoir = ResourceReservoir(self, qty, res_type, regen_rate)
        
    def update(self):
        GameObject.update(self)
        
        if self.res_storage is not None:
            self.res_storage.update()
            
        if self.res_reservoir is not None:
            self.res_reservoir.update()
        
        #update ready workspace reservations
        for res in self.ready_reservations:
            res.update()
            
            if not res.valid:
                res.workspace.release()
                
        self.ready_reservations[:] = [r for r in self.ready_reservations if r.valid]                
        
        #nix invalid reservations
        while len(self.reservations) > 0 and self.reservations[0].valid == False:
            self.reservations.pop(0)
        
        #attempt to fill the first reservation in the list
        if len(self.reservations) > 0:
            res = self.reservations[0]
            for wspace in self.workspaces:
                if not wspace.reserved:
                    res.make_ready( wspace)
                    self.ready_reservations.append( res)
                    self.reservations.pop(0)
                    break
                
        
    def reserve_workspace(self):
        reservation = WorkspaceReservation()
        self.reservations.append( reservation)
        return reservation
    
    def get_available_space(self, tag):
        if self.res_storage is not None:
            return self.res_storage.get_available_space(tag)
        else:
            return 0
    
    def reserve_storage(self, tag, qty):
        if self.res_storage is not None:
            return self.res_storage.reserve(tag, qty)
        else:
            return None


class ResourcePile(StructureObject):
    def update(self):
        StructureObject.update(self)
        self.res_storage.do_decay()
        if self.res_storage.get_contents(None) == 0:
            self.finished = True
