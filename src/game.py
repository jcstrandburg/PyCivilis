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

        for o in self._objects:
            for p in self._objects:
                if o is not p:
                    o.collide_with(p)

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

    def select(self, obj):
        self.selected_obj = obj
        
    def deselect(self, obj):
        if self.selected_obj == obj:
            self.selected_obj = None
            
    """Game specific code"""
    
    def reserve_storage(self, position, reserveThis):
        candidates = []
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "res_storage") and obj.res_storage is not None and obj.res_storage.mode == resource.ResourceStore.WAREHOUSE:
                if obj.res_storage.get_available_space(reserveThis['type']) >= reserveThis['qty']:
                    candidates.append( obj)

        candidates.sort(key=lambda candidate: (candidate.position-position).get_length())
                    
        if ( len(candidates) > 0):
            return candidates[0].res_storage.reserve_storage(reserveThis['type'], reserveThis['qty'])
        return None

    
    def find_forage(self, position, resource_type, qty=1):
        candidates = []
        backups = []
        
        for x in xrange(len(self._objects)):
            obj = self._objects[x]
            if hasattr(obj, "res_storage") and obj.res_storage is not None and obj.res_storage.mode == resource.ResourceStore.RESERVOIR:
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
    
    def reserve_resource_in_storage(self, position, resourceType, qty=1):
        candidates = []
        backups = []
        for obj in self._objects:
            if hasattr(obj, "res_storage") and obj.res_storage is not None and obj.res_storage.mode in (resource.ResourceStore.WAREHOUSE, resource.ResourceStore.DUMP):
                avail = obj.res_storage.get_available_contents(resourceType)
                if avail >= qty:
                    candidates.append( obj)
                elif avail > 0:
                    backups.append( obj)

        candidates.sort(key=lambda candidate: (candidate.position-position).get_length())        
                    
        if ( len(candidates) > 0):
            return candidates[0].res_storage.reserve_resources(resourceType, qty)
        
        backups.sort(key=lambda candidate: (candidate.position-position).get_length())
        
        if ( len(backups) > 0):
            return backups[0].res_storage.reserve_resources(resourceType, backups[0].res_storage.get_available_contents(resourceType))
        
        return None        

            
class GameObject(object):
    """Base class for all objects that exist within the game simulation."""

    def __init__(self, gamemgr, size=(100,100), position=(0,0), mass=10.0):
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
        self.move_speed = 1.0
        self.mass = mass

    def _set_pos(self, pos):
        self.rect.center = self._position = vector.Vec2d(pos)
        
    def _get_pos(self):
        return self._position
        
    position = property( _get_pos, _set_pos, 
                doc="""Center position of the object""")

    def collide_with(self, other):
        if self.rect.colliderect(other.rect):
            self.seperate_from(other)
            other.seperate_from(self)
            
    def seperate_from(self, other):
        move_direction = (self.position - other.position).normalized()
        collide_rect = self.rect.clip(other.rect)
        move_speed = max(collide_rect.w, collide_rect.h)/self.mass
        self.position += move_direction * move_speed

                
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

    def move_toward(self, targ_pos, speed_mult=1.0):
        '''Moves the object towards the target position at the requested multiple of the actors normal walk speed.
        Returns the remaining distance to the target position after the movement is complete'''

        move_rate = self.move_speed * speed_mult
        diff = targ_pos - self.position
        if diff.length < move_rate:
            self.position = targ_pos
        else:
            self.position = self.position.interpolate_to( targ_pos, move_rate/diff.length)
        return self.dist_to(targ_pos)

    def dist_to(self, pos):
        return (pos - self.position).length
            
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
        GameObject.__init__(self, game, (50,50), pos, float('inf'))
        self.reserved = False
        self.struct = structure
        
    def reserve(self):
        self.reserved = True
        
    def release(self):
        self.reserved = False


class BuildingPlacer(GameObject):
    def __init__(self, game, mouse_object, tag):
        GameObject.__init__(self, game, (0,0), mouse_object.position, float('inf'))
        self._mouse_obj = mouse_object
        self._tag = tag
        
    def update(self):
        self.position = self._mouse_obj.position
        
    def place_structure(self):
        self.game.director.add_tagged_structure(self.position, self._tag)
        self.finished = True

        
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

    def __init__(self, game, size=(30,30), position=(0,0), num_workspaces=1):
        GameObject.__init__(self,game,size,position,float('inf'))
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

    def set_storage(self, store):
        assert self.res_storage is None
        self.res_storage = store    
            
    def set_warehouse(self, cap, accepts):
        assert self.res_storage is None
        self.set_storage( resource.ResourceStore(self, cap, accepts, resource.ResourceStore.WAREHOUSE))

    def set_reservoir(self, qty, res_type, regen_rate):
        store = resource.ResourceStore(self, qty, [res_type], resource.ResourceStore.RESERVOIR)
        store.deposit( {'type':res_type, 'qty':qty})
        store.set_delta(res_type, regen_rate)
        self.set_storage( store)         
        
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
    def __init__(self, game, position, dump_this, decayrate):
        StructureObject.__init__(self, game, (0,0), position, 0)
        self.decay_timer = 0
        self.restype = dump_this['type']
        self.decay_rate = decayrate
        
        dump = resource.ResourceStore(self, dump_this['qty'], (dump_this['type'],), resource.ResourceStore.DUMP)
        dump.deposit( dump_this)
        self.set_storage(dump)
       
    
    def update(self):
        self.decay_timer += self.decay_rate*3
        
        if self.decay_timer > self.res_storage.get_actual_contents(self.restype):
            self.res_storage.withdraw(self.restype, self.decay_timer)
            self.decay_timer= 0
        elif self.decay_timer > 1:
            self.res_storage.withdraw(self.restype, 1)
            self.decay_timer -= 1
        
        StructureObject.update(self)
        if self.res_storage.get_actual_contents(None) <= 0:
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
        GameObject.__init__(self, gamemgr, pygame.Rect(0,0,0,0), circuit[0])
        self.dir = 1
        self.move_speed = 0.9
        self.circuit = circuit
        self.circ_node = 0
        self._render_state['movement'] = vector.Vec2d(0,0)
        self.grow_timer = 0
        self.spawn_timer = 0
        self.followers = []
        self.reservations = []
        self.scavenger = None
        
    def set_scavenger(self, scavenger):
        self.scavenger = scavenger
        
    def poach(self, poacher):
        if self.scavenger is not None:
            self.scavenger.chase(poacher)
        
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
            if self.spawn_timer > 50:
                self.add_follower(self.game.director.add_herd_follower(self))
                self.spawn_timer = 0
                
        if self.get_meat() < 3:
            self.grow_timer += 1
            if self.grow_timer > 100:
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
    def __init__(self, gamemgr, herd_follow):
        GameObject.__init__(self, gamemgr, pygame.Rect(0,0,30,30), herd_follow.position)
        self._herd = herd_follow
        self._poacher = None
        self.move_speed = 7.5
        self.dir = 1
        self._render_state['movement'] = vector.Vec2d(0,0)
        self._target_position = None
        
    def update(self):
        GameObject.update(self)
        
        if self._poacher is not None:
            if self._poacher.carrying is not None and self._poacher.carrying['type'] == 'meat':
                if self.move_toward(self._poacher.position, 1.0) < self.move_speed:
                    self._poacher.carrying['qty'] *= 0.5
                    self._poacher = None
            else:
                self._poacher = None
                self._target_position = None
        else:
            if self._target_position is None:
                self._target_position = self._herd.position + (random.uniform(-100,100), random.uniform(100,-100))
            dist = self.move_toward(self._target_position, 0.7)
            if dist < 1:
                self._target_position = None
        
    def chase(self, target):
        self._poacher = target
