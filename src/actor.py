import random

import game


class Actor(game.GameObject):
    """Base class for all game objects that follow orders."""
    
    def __init__(self, gamemgr, pos):
        game.GameObject.__init__(self, gamemgr, (50,50), pos)
        self.move_speed = 5.0
        self._order = None
        self.selectable = True
        self.carrying = None

    def update(self):
        if self._order is not None:
            self._order.do_step()

        if self._order is None or self._order.completed or not self._order.valid:
            self.set_order( IdleOrder(self))
            
        self.game.director.consume_food(0.0015)

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
        self.status = ""
        self.actor = actor
        self.game = actor.game
        self.valid = True
        self.completed = False
        self.progress = 0

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
        self.status = "In state "+state

    def _start_state(self, state):
        return getattr(self, "start_"+state)()

    def _fail_state(self, state):
        fail_method = "fail_"+state
        if hasattr(self, fail_method):
            getattr(self, fail_method)()
        else:
            self.status = "Failure method "+fail_method+" not found"
            self.valid = False

    def _complete_state(self, state):
        complete_method = "complete_"+state
        if hasattr(self, complete_method):
            getattr(self, complete_method)()
        else:
            raise NotImplementedError("Completion method "+complete_method+" not found")
            self.valid = False

    def do_step(self):
        if self._state_order is not None:
            self._state_order.do_step()
            if self._state_order.completed:
                self._complete_state(self._state_name)
            elif not self._state_order.valid:
                self._fail_state(self._state_name)
                
class DebugStatefulOrder(StatefulSuperOrder):
    def set_state(self, state):
        print "Starting state: "+state
        StatefulSuperOrder.set_state(self, state)

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


class ExtractResourceOrder(BaseOrder):
    """Task for simple foraging"""    
    def __init__(self, actor, source, resource_type):
        BaseOrder.__init__(self, actor)
        self._source = source
        self._resource_type = resource_type
        
    def do_step(self):
        actor = self.actor
        self.progress += 0.05
        if self.progress >= 1.0:
            reservoir = actor.target_workspace.struct.res_storage
            actor.carrying = reservoir.withdraw(self._resource_type, 1)
            actor.target_workspace.release()
            actor.forage_reservation.release()
            actor.forage_reservation = None            
            self.completed = True       
            
    def cancel(self):
        actor = self.actor
        if actor.target_workspace is not None:
            actor.target_workspace.release()
            actor.carrying = None
        else:
            print "I'm not sure how we get here cap'n"
            
            
class DepositOrder(BaseOrder):
        
    def do_step(self):
        deposited = False
        actor = self.actor
        if actor.storage_reservation is not None:
            actor.storage_reservation.release()            
            deposited = actor.storage_reservation.structure.res_storage.deposit( actor.carrying)
            actor.storage_reservation = None
    
        if not deposited:
            self.actor.game.director.create_resource_dump(self.actor.position, self.actor.carrying)

        actor.carrying = None
        self.completed = True


class ReserveStorageOrder(BaseOrder):

    def __init__(self, actor):
        BaseOrder.__init__(self, actor)
        self._game = self.actor.game
        
    def do_step(self):
        actor = self.actor
        reservation = self._game.reserve_storage(actor.position, actor.carrying)
        actor.storage_reservation = reservation
        self.completed = True


class WaitForWorkspaceOrder(BaseOrder):
    def __init__(self, actor, structure):
        BaseOrder.__init__(self, actor)
        self._structure = structure
        self._reservation = self._structure.reserve_workspace() 
        self._suborder = IdleOrder(actor)
        
    def do_step(self):
        self._suborder.do_step()

        actor = self.actor
        if self._reservation.ready:
            actor.target_workspace = self._reservation.workspace
            actor.target_workspace.reserve()
            actor.target_workspace
            self.completed = True
        else:
            pass
                    
    def cancel(self):
        BaseOrder.cancel(self)
        self._reservation.release()
 
        
class ReserveForageOrder(BaseOrder):
    def __init__(self, actor, structure, resource_type):
        BaseOrder.__init__(self, actor)
        self._structure = structure
        self._reservation = self._structure.res_storage.reserve_resources(resource_type, 1)
        if self._reservation is None:
            print "Reservation is none, no bueno!"
            self.cancel()
        
    def do_step(self):
        actor = self.actor
        if self._reservation is not None:
            actor.forage_reservation = self._reservation
            self.completed = True
        else:
            pass
                    
    def cancel(self):
        BaseOrder.cancel(self)
        self.actor.forage_reservation = None
        if self._reservation is not None:
            self._reservation.release()


class WaitOrder(BaseOrder):
    def __init__(self, actor, callback):
        BaseOrder.__init__(self, actor)
        self.callback = callback
        self._suborder = IdleOrder(actor)
        
    def do_step(self):
        self._suborder.do_step()
        self.completed = self.callback()


class SeekOrder(BaseOrder):
    def __init__(self, actor, target_obj):
        BaseOrder.__init__(self, actor)
        self._target_obj = target_obj

    def do_step(self):
        dist = self.actor.move_toward( self._target_obj.position, 1.0)
        if dist < 1:
            self.completed = True

class StalkOrder(BaseOrder):
    def __init__(self, actor, target):
        BaseOrder.__init__(self, actor)
        self._target = target
        self._suborder = None
        
    def do_step(self):
        if self.actor.hunt_reservation.ready:
            self.completed = True
            return
        
        if self._suborder is None or self._suborder.completed:
            position = self._target.position + (random.uniform(-100,100), random.uniform(-100,100))
            self._suborder = SimpleMoveOrder(self.actor, position, 0.25)
                
        if self._suborder is not None:
            self._suborder.do_step()


class HuntKillOrder(BaseOrder):
    def __init__(self, actor, target):
        BaseOrder.__init__(self, actor)
        self._target = target
        self._progress = 0

    def do_step(self):
        diff = self._target.position - self.actor.position
        dist = diff.length
        if dist < 20:
            self._progress += 0.05
            if self._progress >= 1:
                self.completed = True
                self.actor.carrying = {'type':'meat', 'qty':1}
                self._target.finished = True
                self._target.leader.poach(self.actor)
        else:
            self.actor.move_toward( self._target.position, 1.0)

class GlobalProduceOrder(BaseOrder):
    def __init__(self, actor, resource_tag):
        BaseOrder.__init__(self, actor)
        self.resource_tag = resource_tag
        
    def do_step(self):
        self.progress += 0.5
        if self.progress >= 1:
            self.completed = True
            self.valid = self.game.director.deposit_to_any_store({'type':self.resource_tag, 'qty': 1})
        

class DoConvertOrder(BaseOrder):
    def __init__(self, actor, fromRes, toRes):
        BaseOrder.__init__(self, actor)
        self.fromRes = fromRes
        self.toRes = toRes
        
    def do_step(self):
        if self.actor.carrying is None or self.actor.carrying['type'] != self.fromRes:
            print "Invalidating DoConvertOrder"
            self.valid = False
            return
        
        self.progress += 0.05/self.actor.carrying['qty']
        if self.progress >= 1:
            self.completed = True
            self.actor.target_workspace.release()
            self.actor.carrying = {'type': self.toRes, 'qty': self.actor.carrying['qty']}

class WithdrawResourceOrder(BaseOrder):
    def __init__(self, actor, bank, resType):
        BaseOrder.__init__(self, actor)
        self.bank = bank
        self.resType = resType
        
    def do_step(self):
        self.actor.carrying = self.bank.res_storage.withdraw(self.resType, 1)
        self.actor.resource_reservation.release()        
        self.actor.resource_reservation = None
        self.completed = True
        
class ReserveResourceInStorageOrder(BaseOrder):
    def __init__(self, actor, resType):
        BaseOrder.__init__(self, actor)
        self.resType = resType
        
    def do_step(self):
        if not hasattr(self.actor, 'resource_reservation') or self.actor.resource_reservation is None:
            self.actor.resource_reservation = self.actor.game.reserve_resource_in_storage(self.actor.position, self.resType, 1)
        
        if self.actor.resource_reservation is None:
            print "cant find resource "+self.resType
            self.valid = False
        else:
            print "fin"
            self.completed = True

class GetResourceFromStorageOrder(StatefulSuperOrder):
    def __init__(self, actor, resource):
        self.resType = resource        
        StatefulSuperOrder.__init__(self, actor, "reserve_resource")
        
    def start_reserve_resource(self):
        return ReserveResourceInStorageOrder(self.actor, self.resType)
    
    def complete_reserve_resource(self):
        self.set_state("move_to_source")
        
    def start_move_to_source(self):
        return SimpleMoveOrder(self.actor, self.actor.resource_reservation.structure.position)
    
    def complete_move_to_source(self):
        self.set_state("withdraw_resource")
        
    def start_withdraw_resource(self):
        return WithdrawResourceOrder(self.actor, self.actor.resource_reservation.structure, self.resType)
    
    def complete_withdraw_resource(self):
        self.completed = True
        
    def cancel(self):
        raise NotImplementedError()


class ForageOrder(StatefulSuperOrder): 

    def __init__(self, actor, target, resource_type):
        self._target = target
        self.resource_type = resource_type
        StatefulSuperOrder.__init__(self, actor, "reserve_forage")
        
    def start_reserve_forage(self):
        return ReserveForageOrder(self.actor, self._target, self.resource_type)

    def complete_reserve_forage(self):
        self.set_state("move_to_forage")

    def fail_reserve_forage(self):
        self._target = self.game.find_forage(self._target.position, self.resource_type, 1)
        if self._target is None:
            self.cancel()
        else:
            self.set_state("reserve_forage")

    def start_move_to_forage(self):
        diff = -self.actor.position + self._target.position
        length = diff.length - 125
        targetpos = self.actor.position.interpolate_to(self._target.position, length/diff.length)
        
        return SimpleMoveOrder(self.actor, targetpos)    

    def complete_move_to_forage(self):
        self.set_state("wait_for_forage_reservation")

    def start_wait_for_forage_reservation(self):
        return WaitOrder(self.actor, lambda: self.actor.forage_reservation.ready)

    def complete_wait_for_forage_reservation(self):
        self.set_state("reserve_forage_workspace")

    def start_reserve_forage_workspace(self):
        return WaitForWorkspaceOrder(self.actor, self._target)

    def complete_reserve_forage_workspace(self):
        self.set_state("move_to_workspace")

    def start_move_to_workspace(self):
        return SimpleMoveOrder(self.actor, self.actor.target_workspace.position)

    def complete_move_to_workspace(self):
        self.set_state("do_forage")

    def start_do_forage(self):
        return ExtractResourceOrder(self.actor,self._target, self.resource_type)

    def complete_do_forage(self):
        self.set_state("reserve_storage")

    def start_reserve_storage(self):
        return ReserveStorageOrder(self.actor)

    def complete_reserve_storage(self):
        self.set_state("move_to_storage")

    def start_move_to_storage(self):
        if self.actor.storage_reservation is not None:
            diff = -self.actor.position + self.actor.storage_reservation.structure.position
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.actor.storage_reservation.structure.position, length/diff.length)            
            return SimpleMoveOrder(self.actor, targetpos)
        else:
            return SimpleMoveOrder(self.actor, (random.uniform(-100.0, 100.0), random.uniform(-100.0, 100.0)))

    def complete_move_to_storage(self):
        self.set_state("store_resources")

    def start_store_resources(self):
        return DepositOrder(self.actor)

    def complete_store_resources(self):
        self.set_state("reserve_forage")
    
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


class HuntOrder(StatefulSuperOrder):
    def __init__(self, actor, target):
        StatefulSuperOrder.__init__(self, actor)
        self._target = target
        self.set_state("seek")

    def start_seek(self):
        return SeekOrder(self.actor, self._target)

    def complete_seek(self):
        self.set_state("reserve_and_stalk")

    def start_reserve_and_stalk(self):
        self.actor.hunt_reservation = self._target.reserve_animal()
        return StalkOrder(self.actor, self._target)

    def complete_reserve_and_stalk(self):
        self.set_state("kill")

    def start_kill(self):
        return HuntKillOrder(self.actor, self.actor.hunt_reservation.animal)

    def complete_kill(self):
        self.actor.hunt_reservation.release()
        self.set_state("reserve_storage")

    def start_reserve_storage(self):
        return ReserveStorageOrder(self.actor)

    def complete_reserve_storage(self):
        self.set_state("seek_storage")

    def start_seek_storage(self):
        if self.actor.storage_reservation is not None:
            diff = -self.actor.position + self.actor.storage_reservation.structure.position
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.actor.storage_reservation.structure.position, length/diff.length)            
            return SimpleMoveOrder(self.actor, targetpos)
        else:
            return SimpleMoveOrder(self.actor, (random.uniform(-100.0, 100.0), random.uniform(-100.0, 100.0)))

    def complete_seek_storage(self):
        self.set_state("dump_storage")

    def start_dump_storage(self):
        return DepositOrder(self.actor)

    def complete_dump_storage(self):
        self.set_state("seek")
        
    def cancel(self):
        StatefulSuperOrder.cancel(self)        
        if hasattr( self.actor, "hunt_reservation") and self.actor.hunt_reservation is not None:
            self.actor.hunt_reservation.release()
            self.actor.hunt_reseravation = None
            

class ConvertResourceOrder(StatefulSuperOrder):
    def __init__(self, actor, target, rawMaterial, finishedGood):
        StatefulSuperOrder.__init__(self, actor)        
        self.targetStruct = target
        self.rawMaterial = rawMaterial
        self.finishedGood = finishedGood
        self.set_state( 'seek_material')
        
    def start_seek_material(self):
        return GetResourceFromStorageOrder(self.actor, self.rawMaterial)

    def complete_seek_material(self):
        self.set_state("move_to_workplace")

    def start_move_to_workplace(self):
        diff = -self.actor.position + self.targetStruct.position
        if diff.length > 125:
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.targetStruct.position, length/diff.length)
        else:
            targetpos = self.actor.position
        
        return SimpleMoveOrder(self.actor, targetpos)

    def complete_move_to_workplace(self):
        self.set_state("wait_for_workspace")

    def start_wait_for_workspace(self):
        return WaitForWorkspaceOrder(self.actor, self.targetStruct)

    def complete_wait_for_workspace(self):
        self.set_state("move_to_workspace")

    def start_move_to_workspace(self):
        return SimpleMoveOrder(self.actor, self.actor.target_workspace.position)

    def complete_move_to_workspace(self):
        self.set_state("do_conversion")

    def start_do_conversion(self):
        return DoConvertOrder(self.actor, self.rawMaterial, self.finishedGood)

    def complete_do_conversion(self):
        self.set_state("reserve_storage")
        
    def start_reserve_storage(self):
        return ReserveStorageOrder(self.actor)

    def complete_reserve_storage(self):
        self.set_state("move_to_storage")

    def start_move_to_storage(self):
        if self.actor.storage_reservation is not None:
            diff = -self.actor.position + self.actor.storage_reservation.structure.position
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.actor.storage_reservation.structure.position, length/diff.length)            
            return SimpleMoveOrder(self.actor, targetpos)
        else:
            return SimpleMoveOrder(self.actor, (random.uniform(-100.0, 100.0), random.uniform(-100.0, 100.0)))

    def complete_move_to_storage(self):
        self.set_state("store_product")        
        
    def start_store_product(self):
        return DepositOrder(self.actor)

    def complete_store_product(self):
        self.set_state("seek_material")
        
    def cancel(self):
        StatefulSuperOrder.cancel(self)


class MeditateOrder(StatefulSuperOrder):
    
    def __init__(self, actor, target):
        StatefulSuperOrder.__init__(self, actor)
        self.target_struct = target
        self.set_state('move_to_workplace')
        
    def start_move_to_workplace(self):
        diff = -self.actor.position + self.target_struct.position
        if diff.length > 125:
            length = diff.length - 125
            targetpos = self.actor.position.interpolate_to(self.target_struct.position, length/diff.length)
        else:
            targetpos = self.actor.position
        
        return SimpleMoveOrder(self.actor, targetpos)

    def complete_move_to_workplace(self):
        self.set_state("wait_for_workspace")

    def start_wait_for_workspace(self):
        return WaitForWorkspaceOrder(self.actor, self.target_struct)

    def complete_wait_for_workspace(self):
        self.set_state("move_to_workspace")

    def start_move_to_workspace(self):
        return SimpleMoveOrder(self.actor, self.actor.target_workspace.position)

    def complete_move_to_workspace(self):
        self.set_state("do_meditation")

    def start_do_meditation(self):
        return GlobalProduceOrder(self.actor, 'spirit')

    def complete_do_meditation(self):
        self.set_state("do_meditation")
        
    def cancel(self):
        StatefulSuperOrder.cancel(self)        


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
            self.selected.set_order( HuntOrder(self.selected, self.target.leader))
        elif tag == 'gather-corn':
            self.selected.set_order( ForageOrder(self.selected, self.target, 'vegetables'))
        elif tag == 'gather-clay':
            self.selected.set_order( ForageOrder(self.selected, self.target, 'clay'))
        elif tag == 'meditate':
            self.selected.set_order( MeditateOrder(self.selected, self.target))
        elif tag == 'make-pots':
            self.selected.set_order( ConvertResourceOrder(self.selected, self.target, 'clay', 'pottery'))
        elif tag == 'make-tools':
            self.selected.set_order( ConvertResourceOrder(self.selected, self.target, 'stone', 'metal_tools'))
        else:
            raise ValueError('Unrecognized tag '+str(tag))
