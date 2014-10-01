import reservation

class Prototype(object):
    def __init__(self, tag, sprite=None, concrete=False):
        self.parent = None
        self.tag = tag
        self.children = {}
        self.sprite = sprite
        self.concrete = concrete
        
    def add_child(self, child):
        self.children[child.tag] = child
        child.parent = self
        
    def add_children(self, children):
        for child in children:
            self.add_child( child)
    
    def find(self, tag):
        if self.tag == tag:
            return self
        elif tag in self.children:
            return self.children[tag]
        elif len(self.children) == 0:
            return None
        else:
            for key in self.children:
                found = self.children[key].find(tag)
                if found is not None:
                    return found
            return None
        
class ResourceReservation(reservation.Reservation):
    def __init__(self, structure, tag, qty):
        reservation.Reservation.__init__(self)
        self.structure = structure
        self.tag = tag
        self.qty = qty        
        
class ResourceStore(object):

    def __init__(self, structure, capacity, accept_list, allow_deposit=True, allow_forage=True):
        self._storage_reservations = []
        self._resource_reservations = []
        self._accepts = list(accept_list)
        self._capacity = capacity
        self._deltas = {}
        self.contents = {}
        self.structure = structure
        self.allow_deposit = allow_deposit
        self.allow_forage = allow_forage

        self.debug_string = 'hey hey hey'

    def set_delta(self, tag, delta):
        self._deltas[tag] = delta

    def withdraw(self, tag, amount):
        try:
            qty = min(self.contents[tag], amount)
            if (qty > 0):
                self.contents[tag] -= amount
                return {'type':tag, 'qty': qty}
            else:
                return None
        except KeyError:
            return None

    def force_deposit(self, resource):
        try:
            self.contents[resource['type']] += resource['qty']
        except KeyError:
            self.contents[resource['type']] = resource['qty']
                
        return True        

    def deposit(self, resource):
        if self.get_actual_space(resource['type']) < resource['qty']:
            return False
                    
        try:
            self.contents[resource['type']] += resource['qty']
        except KeyError:
            if resource['type'] in self._accepts:
                self.contents[resource['type']] = resource['qty']
                
        return True

    def reserve_storage(self, tag, amount):
        cap = self.get_available_space(tag)
        if cap >= amount:
            res = ResourceReservation(self.structure, tag, amount)
            res.make_ready()
            self._storage_reservations.append(res)
            return res
        else:
            return None

    def reserve_resources(self, tag, amount):
        if tag is None:
            tag = self.resource_type
            
        qty = self.get_available_contents(tag)
        res = ResourceReservation(self.structure, tag, amount)
        self._resource_reservations.append(res)
        
        if qty >= amount:
            res.make_ready()
            
        return res

    def get_actual_contents(self, tag=None):
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

    def get_unclaimed_contents(self, tag=None):
        '''Returns the contents that are not accounted for by a 'ready' reservation. 
        These contents may be reserved but no reservation has yet been activated for them'''
                
        content = self.get_actual_contents(tag)
        for res in self._resource_reservations:
            if (res.tag == tag or tag == None) and res.ready:
                content -= res.qty
        return content        

    def get_available_contents(self, tag=None):
        '''Returns the contents that are not accounted for by any reservation, ready or otherwise'''
                
        content = self.get_actual_contents(tag)
        for res in self._resource_reservations:
            if (res.tag == tag or tag == None):
                content -= res.qty
        return content

    def get_actual_space(self, tag):
        if tag is None or tag in self._accepts:
            cap = self._capacity
            for key in self.contents:
                cap -= self.contents[key]
            return cap
        else:
            return 0

    def get_available_space(self, tag):
        space = self.get_actual_space(tag)
        for res in self._storage_reservations:
            space -= res.qty
        return space

    def get_capacity(self):
        return self._capacity

    def do_decay(self):
        for key in self.contents:
            self.contents[key] = max(self.contents[key]-.01, 0)

    def update(self):
        for tag in self._deltas:
            delta = self._deltas[tag]
            if delta > 0:
                qty = min(delta, self.get_available_space(tag))
                if qty > 0:
                    self.deposit( {'type':tag, 'qty':qty})
            elif delta < 0:
                qty = min(self.get_actual_contents(tag), -delta)
                if qty > 0:
                    self.withdraw(tag, qty) 
        
        for r in self._storage_reservations:
            r.update()
        self._storage_reservations[:] = [r for r in self._storage_reservations if r.valid]          

        for r in self._resource_reservations:
            r.update()
        self._resource_reservations[:] = [r for r in self._resource_reservations if r.valid]
        
        pending_res = [r for r in self._resource_reservations if not r.ready]
        for pres in pending_res:
            qty = self.get_unclaimed_contents(pres.tag)
            if qty >= pres.qty:
                pres.make_ready()

def show_tree(base, depth=0):
    output = ""
    for i in xrange(depth):
        output += '  '
    output += '-'
    output += base.tag
    print output
    for key in base.children:
        show_tree(base.children[key], depth+1)
