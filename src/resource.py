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
        
    def find_parent(self, tag):
        if self.tag == tag:
            return self
        elif self.parent is not None:
            return self.parent.find_parent(tag)
        else:
            return None
        
    def flatten_tree(self):
        flat = [self.tag]
        for key in self.children:
            flat += self.children[key].flatten_tree()
        return flat
    
    def flatten_tree_concrete(self):
        if self.concrete:
            flat = [self.tag]
        else:
            flat = []
        for key in self.children:
            flat += self.children[key].flatten_tree_concrete()
        return flat            
        
class ResourceReservation(reservation.Reservation):
    def __init__(self, structure, tag, qty):
        reservation.Reservation.__init__(self)
        self.structure = structure
        self.tag = tag
        self.qty = qty        
        
class ResourceStore(object):

    WAREHOUSE = 16
    RESERVOIR = 17
    DUMP = 18

    def __init__(self, structure, capacity, accept_list, mode=WAREHOUSE):
        self._storage_reservations = []
        self._resource_reservations = []
        self._accepts = list(accept_list)
        self._capacity = capacity
        self._deltas = {}
        self.contents = {}
        self.structure = structure
        self.mode = mode

        self.debug_string = 'hey hey hey'
        
    def accepts(self, tag):
        return tag in self._accepts
     
    def set_delta(self, tag, delta):
        self._deltas[tag] = delta

    def get_delta(self, tag):
        try:
            return self._deltas[tag]
        except KeyError:
            return 0

    def withdraw(self, tag, amount):
        try:
            qty = min(self.contents[tag], amount)
            if (qty > 0):
                self.contents[tag] -= qty
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
            return True            
        except KeyError:
            if resource['type'] in self._accepts:
                self.contents[resource['type']] = resource['qty']
                return True
            
        return False
        

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
            raise ValueError("Cannot reserve resource None")

        if self.accepts(tag):
            qty = self.get_available_contents(tag)
            regen = self.get_delta(tag)

            if qty > 0 or regen > 0:
                res = ResourceReservation(self.structure, tag, amount)
                self._resource_reservations.append(res)
            
                if qty >= amount:
                    res.make_ready()
                
                return res
            else:
                return None
        else:
            return None

    def get_actual_contents(self, tag_or_tags=None):
        if tag_or_tags is None:
            content = 0
            for key in self.contents:
                content += self.contents[key]
            return content
        elif isinstance(tag_or_tags, (basestring, unicode)):
            try:
                return self.contents[tag_or_tags]
            except KeyError:
                return 0
        else:
            content = 0
            for tag in tag_or_tags:
                content += self.get_actual_contents(tag)
            return content
                

    def get_unclaimed_contents(self, tag_or_tags=None):
        '''Returns the contents that are not accounted for by a 'ready' reservation. 
        These contents may be reserved but no reservation has yet been activated for them'''

        if isinstance(tag_or_tags, (basestring, unicode)) or tag_or_tags == None:                
            content = self.get_actual_contents(tag_or_tags)
            for res in self._resource_reservations:
                if (res.tag == tag_or_tags or tag_or_tags == None) and res.ready:
                    content -= res.qty
            return content
        else:
            content = 0
            for tag in tag_or_tags:
                content += self.get_unclaimed_contents(tag)
            return content

    def get_available_contents(self, tag_or_tags=None):
        '''Returns the contents that are not accounted for by any reservation, ready or otherwise'''
                
        if isinstance(tag_or_tags, (basestring, unicode)) or tag_or_tags == None:                
            content = self.get_actual_contents(tag_or_tags)
            for res in self._resource_reservations:
                if (res.tag == tag_or_tags or tag_or_tags == None):
                    content -= res.qty
            return content
        else:
            content = 0
            for tag in tag_or_tags:
                content += self.get_unclaimed_contents(tag)
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

class CompositeResourceStore(ResourceStore):
    def __init__(self, structure, stores=None, mode=ResourceStore.WAREHOUSE):
        self._stores = []
        self._accepts = []
        self.structure = structure
        self.mode = mode
        if stores is not None:
            self.add_stores(stores)
            
    def accepts(self, tag):
        accepts = False
        for store in self._stores:
            accepts = accepts or store.accepts(tag)
        return accepts            

    def add_store(self, store):
        self.add_stores( (store,))
        
    def add_stores(self, stores):
        for store in stores:
            for res in store._accepts:
                if res in self._accepts:
                    raise ValueError("Overlapping resource acceptance: "+str(res))
            self._accepts.extend(store._accepts)
            self._stores.append(store)       

    def set_delta(self, tag, delta):
        for store in self._stores:
            if tag in store._accepts:
                store.set_delta(tag, delta)

    def withdraw(self, tag, amount):
        qty = 0
        
        for store in self._stores:
            avail = store.get_actual_contents(tag)
            if avail > 0:
                res = store.withdraw(tag, amount-qty)
                qty += res['qty']
                
            if qty >= amount:
                break
            
        if qty > 0:
            return {'type':tag, 'qty':qty}
        else:
            return None                

    def force_deposit(self, resource):
        raise NotImplementedError("force_deposit not implemented for CompositeResourceStore")        

    def deposit(self, resource):
        qty = resource['qty']
        for store in self._stores:
            avail = store.get_actual_space(resource['type'])
            dep_qty = min(qty, avail)
            if dep_qty > 0:
                store.deposit( {'type': resource['type'], 'qty':dep_qty})
                qty -= dep_qty
                
            if qty <= 0:
                return True
            
        return False

    def reserve_storage(self, tag, amount):
        for store in self._stores:
            avail = store.get_available_space(tag)
            if avail >= amount:
                return store.reserve_storage(tag, amount)

    def reserve_resources(self, tag, amount):
        for store in self._stores:
            reservation = store.reserve_resources(tag, amount)
            if reservation is not None:
                return reservation
            
        return None

    def get_actual_contents(self, tag=None):
        contents = 0
        for store in self._stores:
            contents += store.get_actual_contents(tag)
        return contents

    def get_unclaimed_contents(self, tag=None):
        '''Returns the contents that are not accounted for by a 'ready' reservation. 
        These contents may be reserved but no reservation has yet been activated for them'''
        contents = 0
        for store in self._stores:
            contents += store.get_unclaimed_contents(tag)
        return contents
    
    def get_available_contents(self, tag=None):
        '''Returns the contents that are not accounted for by any reservation, ready or otherwise'''
        contents = 0
        for store in self._stores:
            contents += store.get_available_contents(tag)
        return contents

    def get_actual_space(self, tag):
        space = 0
        for store in self._stores:
            space += store.get_actual_space(tag)
        return space

    def get_available_space(self, tag):
        space = 0
        for store in self._stores:
            space += store.get_available_space(tag)
        return space
    
    def get_capacity(self):
        cap = 0
        for store in self._stores:
            cap += store.get_capacity()
        return cap

    def update(self):
        for store in self._stores:
            store.update()

def show_tree(base, depth=0):
    output = ""
    for i in xrange(depth):
        output += '  '
    output += '-'
    output += base.tag
    print output
    for key in base.children:
        show_tree(base.children[key], depth+1)
