import pygame, math
import random
from collections import deque

import vector
import reservation
import resource

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
    
    def reserve_storage(self, position, resource):
        candidates = []
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "res_storage") and obj.res_storage is not None and obj.res_storage.allow_deposit:
                if obj.res_storage.get_available_space(resource['type']) >= resource['qty']:
                    candidates.append( obj)

        candidates.sort(key=lambda candidate: (candidate.position-position).get_length())
                    
        if ( len(candidates) > 0):
            return candidates[0].res_storage.reserve_storage(resource['type'], resource['qty'])
        return None

    
    def find_forage(self, position, resource_type, qty=1):
        candidates = []
        backups = []
        
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "res_storage") and obj.res_storage is not None and obj.res_storage.allow_forage:
                avail = obj.res_storage.get_available_contents(resource_type)
                if avail >= qty:
                    candidates.append( obj)
                elif avail > 0 or obj.res_storage.get_delta(resource_type) > 0:
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

    def __init__(self, gamemgr, size=(100,100), position=(0,0)):
        """Initialize with the given game."""
        self.finished = False
        self.rect = pygame.Rect(0,0,size[0],size[1])
        self.rect.center = position
        self._position = vector.Vec2d( position)
        self.game = gamemgr
        self._selected = False
        self.id = gamemgr.new_object_id()
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
        
class WorkspaceReservation(reservation.Reservation):
    def __init__(self):
        reservation.Reservation.__init__(self)
        self.workspace = None
        
    def make_ready(self, workspace):
        reservation.Reservation.make_ready(self)
        self.workspace = workspace

    def release(self):
        reservation.Reservation.release(self)
        if self.workspace is not None:
            self.workspace.release()

class StructureObject(GameObject):

    def __init__(self, game, size=(100,100), position=(0,0), num_workspaces=1):
        GameObject.__init__(self,game,size,position)
        self.workspaces = []
        self.reservations = []
        self.ready_reservations = []
        self.res_storage = None
        
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
        assert self.res_storage is None
        self.res_storage = resource.ResourceStore(self, cap, accepts, True, False)

    def set_reservoir(self, qty, res_type, regen_rate):
        assert self.res_storage is None        
        self.res_storage = resource.ResourceStore(self, qty, [res_type], False, True)
        self.res_storage.deposit( {'type':res_type, 'qty':qty})
        self.res_storage.set_delta(res_type, regen_rate)
        
    def update(self):
        GameObject.update(self)
        
        if self.res_storage is not None:
            self.res_storage.update()
        
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
        if self.res_storage.get_actual_contents(None) == 0:
            self.finished = True

class HuntingReservation(reservation.Reservation):
    def __init__(self):
        self.animal = None
        reservation.Reservation.__init__(self)
        
    def make_ready(self, animal):
        self.animal = animal
        reservation.Reservation.make_ready(self)
        

class HerdMember(GameObject):
    def __init__(self, leader):
        self.leader = leader
        self.target = leader.position
        self.move_speed = 1.1
        GameObject.__init__(self, leader.game, pygame.Rect(0,0,30,30), self.leader.position)
        self._render_state['adult'] = self.adult = False
        
    def update(self):
        diff = self.target - self.position
        if diff.length <= self.move_speed:
            x = 175
            self.target = self.leader.position + (random.uniform(-x,x), random.uniform(-x,x))
        else:
            self.position = self.position.interpolate_to( self.target, self.move_speed/diff.length)
            
    def mature(self):
        self._render_state['adult'] = self.adult = True           

class HerdObject(GameObject):
    def __init__(self, gamemgr, circuit):
        GameObject.__init__(self, gamemgr, pygame.Rect(0,0,30,30), circuit[0])
        self.dir = 1
        self.move_speed = 0.9
        self.circuit = circuit
        self.circ_node = 0
        self._render_state['movement'] = vector.Vec2d(0,0)
        self.grow_timer = 0
        self.spawn_timer = 0
        self.followers = []
        self.reservations = []
        
    def update(self):
        GameObject.update(self)

        diff = self.circuit[self.circ_node] - self.position
        if diff.length <= self.move_speed:
            self.circ_node = (self.circ_node + 1)%len(self.circuit)
        else:
            self.position = self.position.interpolate_to( self.circuit[self.circ_node], self.move_speed/diff.length)

        '''do regeneration'''            
        self.followers = [follower for follower in self.followers if not follower.finished]
        
        if len( self.followers) < 3:
            self.spawn_timer += 1
            if self.spawn_timer > 150:
                self.add_follower(self.game.director.add_herd_follower(self))
                self.spawn_timer = 0
                
        if self.get_meat() < 3:
            self.grow_timer += 1
            if self.grow_timer > 500:
                self.grow_timer = 0
                for follower in self.followers:
                    if not follower.adult:
                        follower.mature()
                        break
                    
        if len(self.reservations) > 0:
            if not self.reservations[0].valid:
                del self.reservations[0] 
            elif not self.reservations[0].ready:
                for follower in self.followers:
                    if follower.adult:
                        self.reservations[0].make_ready(follower)
            

    def add_follower(self, follower):
        self.followers.append(follower)

    def get_meat(self):
        meat = 0
        for follower in self.followers:
            if follower.adult:
                meat += 1
                
        return meat
    
    def reserve_animal(self):
        res = HuntingReservation()
        self.reservations.append(res)
        return res
                
        
class ScavengerObject(GameObject):
    def __init__(self, gamemgr, position, herd_follow):
        self._herd_follow = herd_follow
        GameObject.__init__(self, gamemgr, pygame.Rect(0,0,30,30), position)
        self.dir = 1
        self._render_state['movement'] = vector.Vec2d(0,0)
