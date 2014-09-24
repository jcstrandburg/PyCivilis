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
            if self._task.is_completed():
                self._task = None

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
    
    def __init__(self, actor):
        self._completed = False
        self.actor = actor
        
    def do_step(self):
        raise NotImplementedError("Task.do_step")
        
    def is_completed(self):
        return self._completed
        
    def cancel(self):
        print "Task.cancel not implemented"

class SimpleMoveTask(Task):
    """Task for simple straight line movement"""
    
    def __init__(self, actor, dest, moveratio=1.0):
        Task.__init__(self, actor)
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
    def __init__(self, actor, dest):
        newdest = vector.Vec2d(dest) + (random.uniform(-10.0, 10.0), random.uniform(-10.0, 10.0))    
        SimpleMoveTask.__init__(self, actor, newdest, 0.1)
        
        
class ForageTask(Task):
    """Task for simple foraging"""    
    def __init__(self, actor, source):
        Task.__init__(self, actor)
        self._source = source
        
    def do_step(self):
        actor = self.actor
        if actor.carrying is None or actor.carrying['type'] != 'stone':
            actor.carrying = {'type':"stone", 'qty':0}
        
        actor.carrying['qty'] += .3
    
        if actor.carrying['qty'] >= 1.0:
            actor.carrying['qty'] = 1.0
            actor.target_workspace.release()
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
            deposited = actor.storage_reservation.structure.res_storage.deposit( actor.carrying['type'], actor.carrying['qty'])
            actor.storage_reservation = None
    
        if not deposited:
            self.actor.game.controller.create_resource_dump(self.actor.position, self.actor.carrying)

        actor.carrying = None
        self._completed = True

class ReserveStorageTask(Task):

    def __init__(self, actor, game):
        Task.__init__(self, actor)
        self._game = game
        
    def do_step(self):
        actor = self.actor
        reservation = self._game.reserve_storage(actor.position, actor.carrying)
        actor.storage_reservation = reservation
        self._completed = True

class ReserveWorkspaceTask(Task):
    def __init__(self, actor, structure):
        Task.__init__(self, actor)
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
        self._reservation.release()
        
class Order(object):
    """Base class for all order classes. Implements a sort of state
    machine functionality for transitioning and cycling between tasks."""
    
    def __init__(self, actor, game):
        self.actor = actor
        self.game = game
        self._task_state = None
        self._task = None

    def get_task(self):
        if self._task_state is not None:
            self._task = self._task_state()
            return self._task
        else:
            return None
            
    def cancel(self):
        if self._task is not None:
            self._task.cancel()

            
class MoveOrder(Order):
    """Class that handles move orders, including wandering functionality
    at the final destination."""

    def __init__(self, actor, game, dest):
        Order.__init__(self, actor, game)
        self._dest = vector.Vec2d(dest)
        self._task_state = self._state_seek
        
    def _state_seek(self):
        self._task_state = self._state_wander
        return SimpleMoveTask(self.actor, self._dest)

    def _state_wander(self):
        self.task_state = self._state_wander
        return WanderTask(self.actor, self._dest)
        
    def cancel(self):
        Order.cancel(self)
        
class ForageOrder(Order): 

    def __init__(self, actor, game, target):
        Order.__init__(self, actor, game)
        self._task_state = self._state_seek_forage_location
        self._target = target
        
    def _state_seek_forage_location(self):
        diff = -self.actor.position + self._target.position
        length = diff.length - 125
        targetpos = self.actor.position.interpolate_to(self._target.position, length/diff.length)
        
        self._task_state = self._state_reserve_forage_workspace
        return SimpleMoveTask(self.actor, targetpos)    
        
    def _state_reserve_forage_workspace(self):
        self._task_state = self._state_seek_workspace
        return ReserveWorkspaceTask(self.actor, self._target)
        
    def _state_seek_workspace(self):
        self._task_state = self._state_do_forage
        return SimpleMoveTask(self.actor, self.actor.target_workspace.position)
    
    def _state_do_forage(self):
        self._task_state = self._state_reserve_storage
        return ForageTask(self.actor, self._target)
        
    def _state_reserve_storage(self):
        self._task_state = self._state_seek_storage
        return ReserveStorageTask(self.actor, self.game)
        
    def _state_seek_storage(self):
        self._task_state = self._state_dump_storage
        if self.actor.storage_reservation is not None:
            return SimpleMoveTask(self.actor, self.actor.storage_reservation.structure.position)
        else:
            return SimpleMoveTask(self.actor, (random.uniform(-100.0, 100.0), random.uniform(-100.0, 100.0)))
        
    def _state_dump_storage(self):
        self._task_state = self._state_seek_forage_location
        return DumpTask(self.actor)
        
    def cancel(self):
        Order.cancel(self)
        if self.actor.target_workspace is not None:
            self.actor.target_workspace.release()
            self.actor.target_workspace = None
        
class OrderBuilder(object):
    def __init__(self, selected, target):
        self.selected = selected
        self.target = target

    def get_options(self):
        return self.target.target_actions.intersection( self.selected.abilities)    
        
    def do_order(self, tag):
        if tag == "mine" or tag == "cut-wood":
            self.selected.set_order( ForageOrder(self.selected, self.selected.game, self.target))
        print tag
