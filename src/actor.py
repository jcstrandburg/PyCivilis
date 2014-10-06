import random

import game
import vector

class Actor(game.GameObject):
    """Base class for all game objects that follow orders."""
    
    def __init__(self, gamemgr, pos):
        game.GameObject.__init__(self, gamemgr, (50,50), pos)
        self.move_speed = 5.0
        self._order = None
        self.selectable = True
        self.carrying = None

    def move_toward(self, targ_pos, speed_mult=1.0):
        '''Moves the actor towards the target position at the requested multiple of the actors normal walk speed.
        Returns the remaining distance to the target position after the movement is complete'''

        move_rate = self.move_speed * speed_mult
        diff = targ_pos - self.position
        if diff.length < move_rate:
            self.position = targ_pos
        else:
            self.position = self.position.interpolate_to( targ_pos, move_rate/diff.length)
        return (targ_pos - self.position).length

    def update(self):
        if self._order is not None:
            self._order.do_step()

        if self._order is None or self._order.completed or not self._order.valid:
            print self._order
            self.set_order( IdleOrder(self))

    def set_order(self, order):
        if self._order is not None:
            self._order.cancel()
        self._order = order
                
    def selectable(self):
        return True
        
    def select(self):
        game.GameObject.select(self)
        
    def deselect(self):
        game.GameObject.deselect(self)

class BaseOrder(object):
    def __init__(self, actor):
        self.actor = actor
        self.game = actor.game
        self.valid = True
        self.completed = False

    def do_step(self):
        raise NotImplementedError("abstract class!")

    def cancel(self):
        self.valid = False

class DummyOrder(BaseOrder):
    def do_step(self):
        self.completed = True

class StatefulSuperOrder(BaseOrder):
    def __init__(self, actor, state=None):
        BaseOrder.__init__(self, actor)
        self._state_name = None
        self._state_order = None
        if state is not None:
            self.set_state(state)        

    def set_state(self, state):
        self._state_name = state
        self._state_order = self._start_state(state)

    def _start_state(self, state):
        return getattr(self, "start_"+state)()

    def _fail_state(self, state):
        fail_method = "fail_"+state
        if hasattr(self, fail_method):
            getattr(self, fail_method)()
        else:
            self.valid = False

    def _complete_state(self, state):
        complete_method = "complete_"+state
        if hasattr(self, complete_method):
            getattr(self, complete_method)()
        else:
            self.valid = False

    def do_step(self):
        if self._state_order is not None:
            self._state_order.do_step()
            if self._state_order.completed:
                self._complete_state(self._state_name)
            elif not self._state_order.valid:
                self._fail_state(self._state_name)

class SimpleMoveOrder(BaseOrder):
    def __init__(self, actor, targ_pos, move_rate=1.0):
        BaseOrder.__init__(self, actor)
        self.targ_pos = targ_pos
        self.move_rate = move_rate

    def do_step(self):
        dist = self.actor.move_toward( self.targ_pos, self.move_rate)
        if dist < 1:
            self.completed = True



class IdleOrder(StatefulSuperOrder):
    def __init__(self, actor):
        self.idle_center = actor.position       
        StatefulSuperOrder.__init__(self, actor, "idle")

    def start_idle(self):
        idle_range = 30
        position = (self.idle_center[0] + random.uniform(-idle_range, idle_range), self.idle_center[1] + random.uniform(-idle_range, idle_range))
        return SimpleMoveOrder(self.actor, position, 0.1)

    def complete_idle(self):
        self.set_state('idle')














class ForageOrder(StatefulSuperOrder): 

    def __init__(self, actor, target, resource_type):
        self._target = target
        self.resource_type = resource_type
        StatefulSuperOrder.__init__(self, actor, "reserve_forage")
        
    def start_reserve_forage(self):
        return DummyOrder(self.actor)

    def complete_reserve_forage(self):
        self.set_state("move_to_forage")

    def start_move_to_forage(self):
        return DummyOrder(self.actor)

    def complete_move_to_forage(self):
        self.set_state("wait_for_forage_reservation")

    def start_wait_for_forage_reservation(self):
        return DummyOrder(self.actor)

    def compete_wait_for_forage_reservation(self):
        self.set_state("reserve_forage_workspace")

    def start_reserve_forage_workspace(self):
        return DummyOrder(self.actor)

    def complete_reserve_forage_workspace(self):
        self.set_state("move_to_workspace")

    def start_move_to_workspace(self):
        return DummyOrder(self.actor)

    def complete_move_to_workspace(self):
        self.set_state("do_forage")

    def start_do_forage(self):
        return DummyOrder(self.actor)

    def complete_do_forage(self):
        self.set_state("reserve_storage")

    def start_reserve_storage(self):
        return DummyOrder(self.actor)

    def complete_reserve_storage(self):
        self.set_state("move_to_storage")

    def start_move_to_storage(self):
        return DummyOrder(self.actor)

    def complete_move_to_storage(self):
        self.set_state("store_resources")

    def start_store_resources(self):
        return DummyOrder(self.actor)

    def complete_store_resources(self):
        self.set_state("reserve_forage")

    def start_seek_new_reservoir(self):
        return DummyOrder(self.actor)

    def complete_seek_new_reservoir(self):
        self.set_state("move_to_forage")

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
        self._target = self.game.find_forage(self.actor.position, self._target.res_storage.resource_type, 1)
        if self._target is None:
            self.cancel()
        
    def cancel(self):
        StatefulSuperOrder.cancel(self)
        if hasattr(self.actor, 'target_workspace') and self.actor.target_workspace is not None:
            self.actor.target_workspace.release()
            self.actor.target_workspace = None
        if hasattr(self.actor, 'storage_reservation') and self.actor.storage_reservation is not None:
            self.actor.storage_reservation.release()
            self.actor.storage_reservation = None
        if hasattr(self.actor, 'forage_reservation') and self.actor.forage_reservation is not None:
            self.actor.forage_reservation.release()
            self.actor.forage_reservation = None   













'''
Old shit, kill it with fire
'''




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
        dist = actor.move_toward( self._dest, self._moveratio)
        if dist < 1:
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
        self._progress += 0.5
        if self._progress >= 1.0:
            reservoir = actor.target_workspace.struct.res_storage
            actor.carrying = reservoir.withdraw(self.order.resource_type, 1)
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
        self._reservation = self._structure.res_storage.reserve_resources(order.resource_type, 1)
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


class SeekTask(Task):
    def __init__(self, order, actor, target_obj):
        Task.__init__(self, order, actor)
        self._target_obj = target_obj

    def do_step(self):
        dist = self.actor.move_toward( self._target_obj.position, 1.0)
        if dist < 1:
            self._completed = True

class HuntKillTask(Task):
    def __init__(self, order, actor, target):
        Task.__init__(self, order, actor)
        self._target = target
        self._progress = 0

    def do_step(self):
        self._progress += 0.05
        if self._progress >= 1:
            self._completed = True
            self.actor.carrying = {'type':'meat', 'qty':1}
        
        
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
            
class HuntOrder(Order):
    def __init__(self, actor, game, target):
        Order.__init__(self, actor, game)
        self._target = target
        self._task_state = self._state_seek

    def _state_seek(self):
        self._task_state = self._state_reserve
        return SeekTask(self, self.actor, self._target)

    def _state_reserve(self):
        self._task_state = self._state_kill
        return WaitTask(self, self.actor, lambda: True)

    def _state_kill(self):
        self._task_state = self._state_reserve_storage
        return HuntKillTask(self, self.actor, self._target)

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
        self._task_state = self._state_seek
        return DumpTask(self, self.actor)
    
            
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
        
"""class ForageOrder(Order): 

    def __init__(self, actor, game, target, resource_type):
        Order.__init__(self, actor, game)
        self._task_state = self._state_reserve_forage
        self._target = target
        self.resource_type = resource_type
        
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
        self._target = self.game.find_forage(self.actor.position, self._target.res_storage.resource_type, 1)
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
            self.actor.forage_reservation = None"""           
        



'''we need this, don't get rid of it'''
class OrderBuilder(object):
    def __init__(self, selected, target):
        self.selected = selected
        self.target = target

    def get_options(self):
        return self.target.target_actions.intersection( self.selected.abilities)    
        
    def do_order(self, tag):
        if tag == "mine":
            self.selected.set_order( ForageOrder(self.selected, self.target, 'stone'))
        elif tag == "cut-wood":
            self.selected.set_order( ForageOrder(self.selected, self.target, 'wood'))
        elif tag == "hunt":
            self.selected.set_order( HuntOrder(self.selected, self.target))
        else:
            raise ValueError('Unrecognized tag '+str(tag))
