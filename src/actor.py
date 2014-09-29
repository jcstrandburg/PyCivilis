import random

import game
import vector

class Actor(game.GameObject):
    """Base class for all game objects that follow orders."""
    
    def __init__(self, gamemgr, pos):
        game.GameObject.__init__(self, gamemgr, (50,50), pos)
        self.move_speed = 5.0
        self._task = None
        self._order = None
        self.selectable = True
        self.carrying = None

    def update(self):   
        if self._task is None:
            if self._order is not None:
                self._task = self._order.get_task()
                if self._task is None:
                    self._order = None

        if self._task is not None:
            self._task.do_step()
            if self._task.is_completed() or not self._task.valid:
                self._task = None
                
        if self._order is None or not self._order.valid:
            self.set_order( MoveOrder(self, self.game, self.position))

    def set_order(self, order):
        self._task = None
        if self._order is not None:
            self._order.cancel()
        self._order = order
                
    def selectable(self):
        return True
        
    def select(self):
        game.GameObject.select(self)
        
    def deselect(self):
        game.GameObject.deselect(self)

class Task(object):
    """Base class for all task classes."""
    
    def __init__(self, order, actor):
        self._completed = False
        self.valid = True
        self.order = order
        self.actor = actor
        
    def do_step(self):
        raise NotImplementedError("Task.do_step")
        
    def is_completed(self):
        return self._completed
        
    def cancel(self):
        self.valid = False

class SimpleMoveTask(Task):
    """Task for simple straight line movement"""
    
    def __init__(self, order, actor, dest, moveratio=1.0):
        Task.__init__(self, order, actor)
        self._dest = vector.Vec2d(dest)
        self._moveratio = moveratio
        
    def do_step(self):
        actor = self.actor
        pos = actor.position
        diff = self._dest - pos
        move_speed = actor.move_speed*self._moveratio
        if diff.length > move_speed:
            actor.position = pos.interpolate_to( self._dest, move_speed/diff.length)
        else:
            actor.position = self._dest
            self._completed = True
            
    def cancel(self):
        pass
            
class WanderTask(SimpleMoveTask):
    def __init__(self, order, actor, dest):
        newdest = vector.Vec2d(dest) + (random.uniform(-10.0, 10.0), random.uniform(-10.0, 10.0))    
        SimpleMoveTask.__init__(self, order, actor, newdest, 0.1)
        
        
class ForageTask(Task):
    """Task for simple foraging"""    
    def __init__(self, order, actor, source):
        Task.__init__(self, order, actor)
        self._source = source
        self._progress = 0
        
    def do_step(self):
        actor = self.actor
        self._progress += 0.02
        if self._progress >= 1.0:
            reservoir = actor.target_workspace.struct.res_reservoir
            actor.carrying = reservoir.withdraw(reservoir.resource_type, 1)
            actor.target_workspace.release()
            actor.forage_reservation.release()
            actor.forage_reservation = None            
            self._completed = True       
            
    def cancel(self):
        actor = self.actor
        if actor.target_workspace is not None:
            actor.target_workspace.release()
            actor.carrying = None
        else:
            print "I'm not sure how we get here cap'n"
            
            
class DumpTask(Task):
        
    def do_step(self):
        deposited = False
        actor = self.actor
        if actor.storage_reservation is not None:
            actor.storage_reservation.release()            
            deposited = actor.storage_reservation.structure.res_storage.deposit( actor.carrying)
            actor.storage_reservation = None
    
        if not deposited:
            self.actor.game.controller.create_resource_dump(self.actor.position, self.actor.carrying)

        actor.carrying = None
        self._completed = True

class ReserveStorageTask(Task):

    def __init__(self, order, actor, game):
        Task.__init__(self, order, actor)
        self._game = game
        
    def do_step(self):
        actor = self.actor
        reservation = self._game.reserve_storage(actor.position, actor.carrying)
        actor.storage_reservation = reservation
        self._completed = True

class ReserveWorkspaceTask(Task):
    def __init__(self, order, actor, structure):
        Task.__init__(self, order, actor)
        self._structure = structure
        self._reservation = self._structure.reserve_workspace()
        
    def do_step(self):
        actor = self.actor
        if self._reservation.ready:
            actor.target_workspace = self._reservation.workspace
            actor.target_workspace.reserve()
            actor.target_workspace
            self._completed = True
        else:
            pass
                    
    def cancel(self):
        Task.cancel(self)
        self._reservation.release()
        
class ReserveForageTask(Task):
    def __init__(self, order, actor, structure):
        Task.__init__(self, order, actor)
        self._structure = structure
        self._reservation = self._structure.res_reservoir.reserve()
        if self._reservation is None:
            self.order.seek_new_reservoir()
            self.cancel()
        
    def do_step(self):
        actor = self.actor
        if self._reservation is not None:
            actor.forage_reservation = self._reservation
            self._completed = True
        else:
            pass
                    
    def cancel(self):
        Task.cancel(self)
        self.actor.forage_reservation = None
        if self._reservation is not None:
            self._reservation.release()

class WaitTask(Task):
    def __init__(self, order, actor, callback):
        Task.__init__(self, order, actor)
        self.callback = callback
        
    def do_step(self):
        self._completed = self.callback()
        
class Order(object):
    """Base class for all order classes. Implements a sort of state
    machine functionality for transitioning and cycling between tasks."""
    
    def __init__(self, actor, game):
        self.actor = actor
        self.game = game
        self._task_state = None
        self._task = None
        self.valid = True

    def get_task(self):
        if self.valid and self._task_state is not None:
            self._task = self._task_state()
            return self._task
        else:
            return None
            
    def cancel(self):
        if self._task is not None:
            self._task.cancel()
        self.valid = False
            

            
class MoveOrder(Order):
    """Class that handles move orders, including wandering functionality
    at the final destination."""

    def __init__(self, actor, game, dest):
        Order.__init__(self, actor, game)
        self._dest = vector.Vec2d(dest)
        self._task_state = self._state_seek
        
    def _state_seek(self):
        self._task_state = self._state_wander
        return SimpleMoveTask(self, self.actor, self._dest)

    def _state_wander(self):
        self.task_state = self._state_wander
        return WanderTask(self, self.actor, self._dest)
        
class ForageOrder(Order): 

    def __init__(self, actor, game, target):
        Order.__init__(self, actor, game)
        self._task_state = self._state_reserve_forage
        self._target = target
        
    def _state_reserve_forage(self):
        self._task_state = self._state_seek_forage_location
        return ReserveForageTask(self, self.actor, self._target)
        
    def _state_seek_forage_location(self):
        diff = -self.actor.position + self._target.position
        length = diff.length - 125
        targetpos = self.actor.position.interpolate_to(self._target.position, length/diff.length)
        
        self._task_state = self._state_wait_for_forage_reservation
        return SimpleMoveTask(self, self.actor, targetpos)    

    def _state_wait_for_forage_reservation(self):
        self._task_state = self._state_reserve_forage_workspace
        return WaitTask(self, self.actor, lambda: self.actor.forage_reservation.ready)
        
    def _state_reserve_forage_workspace(self):
        self._task_state = self._state_seek_workspace
        return ReserveWorkspaceTask(self, self.actor, self._target)
        
    def _state_seek_workspace(self):
        self._task_state = self._state_do_forage
        return SimpleMoveTask(self, self.actor, self.actor.target_workspace.position)
    
    def _state_do_forage(self):
        self._task_state = self._state_reserve_storage
        return ForageTask(self, self.actor, self._target)
        
    def _state_reserve_storage(self):
        if self.actor.carrying is None:
            self.cancel()
            return None
            
        self._task_state = self._state_seek_storage
        return ReserveStorageTask(self, self.actor, self.game)
        
    def _state_seek_storage(self):
        self._task_state = self._state_dump_storage
        if self.actor.storage_reservation is not None:
            diff = -self.actor.position + self.actor.storage_reservation.structure.position
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.actor.storage_reservation.structure.position, length/diff.length)            
            return SimpleMoveTask(self, self.actor, targetpos)
        else:
            return SimpleMoveTask(self, self.actor, (random.uniform(-100.0, 100.0), random.uniform(-100.0, 100.0)))
        
    def _state_dump_storage(self):
        self._task_state = self._state_reserve_forage
        return DumpTask(self, self.actor)
    
    def seek_new_reservoir(self):
        self._task_state = self._state_reserve_forage        
        self._target = self.game.find_reservoir(self.actor.position, self._target.res_reservoir.resource_type, 1)
        print self._target
        if self._target is None:
            self.cancel()
        
    def cancel(self):
        Order.cancel(self)
        if hasattr(self.actor, 'target_workspace') and self.actor.target_workspace is not None:
            self.actor.target_workspace.release()
            self.actor.target_workspace = None
        if hasattr(self.actor, 'storage_reservation') and self.actor.storage_reservation is not None:
            self.actor.storage_reservation.release()
            self.actor.storage_reservation = None
        if hasattr(self.actor, 'forage_reservation') and self.actor.forage_reservation is not None:
            self.actor.forage_reservation.release()
            self.actor.forage_reservation = None            
        
class OrderBuilder(object):
    def __init__(self, selected, target):
        self.selected = selected
        self.target = target

    def get_options(self):
        return self.target.target_actions.intersection( self.selected.abilities)    
        
    def do_order(self, tag):
        if tag == "mine" or tag == "cut-wood":
            self.selected.set_order( ForageOrder(self.selected, self.selected.game, self.target))
