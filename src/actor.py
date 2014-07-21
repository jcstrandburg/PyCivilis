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

    def update(self):   
        if self._task is None:
            if self._order is not None:
                self._task = self._order.get_task()
                if self._task is None:
                    self._order = None

        if self._task is not None:
            self._task.do_step(self)
            if self._task.is_completed():
                self._task = None

    def set_order(self, order):
        self._task = None
        self._order = order
                
    def selectable(self):
        return True
        
    def select(self):
        game.GameObject.select(self)
        
    def deselect(self):
        game.GameObject.deselect(self)
        

class Task(object):
    """Base class for all task classes."""
    
    def __init__(self):
        self._completed = False
        
    def do_step(self, actor):
        raise NotImplementedError("Task.do_step")
        
    def is_completed(self):
        return self._completed
        

class SimpleMoveTask(Task):
    """Task for simple straight line movement"""
    
    def __init__(self, dest, moveratio=1.0):
        Task.__init__(self)
        self._dest = vector.Vec2d(dest)
        self._moveratio = moveratio
        
    def do_step(self, actor):
        pos = actor.position
        diff = self._dest - pos
        move_speed = actor.move_speed*self._moveratio
        if diff.length > move_speed:
            actor.position = pos.interpolate_to( self._dest, move_speed/diff.length)
        else:
            actor.position = self._dest
            self._completed = True
            

class Order(object):
    """Base class for all order classes. Implements a sort of state
    machine functionality for transitioning and cycling between tasks."""
    
    def __init__(self, actor, game):
        self.actor = actor
        self.game = game
        self._task_state = None

    def get_task(self):
        if self._task_state is not None:
            return self._task_state()
        else:
            return None
            

class MoveOrder(Order):
    """Class that handles move orders, including wandering functionality
    at the final destination."""

    def __init__(self, actor, game, dest):
        Order.__init__(self, actor, game)
        self._dest = vector.Vec2d(dest)
        self._task_state = self._state_seek
        
    def _state_seek(self):
        self._task_state = self._state_wander
        return SimpleMoveTask(self._dest)

    def _state_wander(self):
        self.task_state = self._state_wander
        dest = self._dest + (random.uniform(-50.0, 50.0), random.uniform(-50.0, 50.0))
        return SimpleMoveTask(dest, 0.3)