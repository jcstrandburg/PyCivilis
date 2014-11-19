import vector

import math

class PathMap(object):
    def __init__(self, tiles):
        self.shape = len(tiles), len(tiles[0])
        self.tiles = tiles
        
    def pos_to_tile(self, pos):
        pass
    
    def tile_to_pos(self, pos):
        pass
    
    def valid_tile(self, tile):
        if tile[0] >= 0 and tile[1] >= 0 and tile[0] < self.shape[1] and tile[1] < self.shape[0]:
            return True
        else:
            return False
    
    def neighbor_tiles(self, tile):
        borders = ((0,1),(0,-1),(1,0),(-1,0))
        neighbors = []
        
        for b in borders:
            candidate = (tile[0]+b[0],tile[1]+b[1])
            if self.valid_tile(candidate):
                neighbors.append(candidate)
                
        return neighbors
    
    def tile_passable(self, tile):
        return self.tiles[tile[1]][tile[0]] == 0
    
    def tile_cost(self, tile):
        return 1
    
    def walkable(self, start, finish):
        if start == finish:
            return True
        
        start = vector.Vec2d(start)
        finish = vector.Vec2d(finish)
        diff = finish - start
        diff_length = diff.length
        
        progress = 0.0
        while progress <= diff_length:
            sample = start + (progress/diff_length)*diff + (0.5, 0.5)
            #print sample, sample.int_tuple
            if not self.tile_passable(sample.int_tuple):
                return False
            
            progress += 0.2
            
        return True           
        

class PathFinder(object):
    
    def __init__(self, origin, dest, map):
        self.origin = origin
        self.dest = dest
        self.map = map
        
        self.closed_set = set()
        self.open_set = set()
        self.came_from = {}
        
        self.g_score = {}
        self.g_score[origin] = 0
        self.f_score = {}
        self.f_score[origin] = self.g_score[origin] + self.h_cost(origin, dest)
        
        self.open_set.add(origin)
                
    def h_cost(self, u, v):
        return abs(v[0]-u[0]) + abs(v[1]-u[1])
    
    def actual_cost(self, u, v):
        return math.sqrt( (v[1]-u[1])**2 + (v[0]-u[0])**2)

    def simplify(self, the_path):
        simple_path = [the_path[0]]
        current = the_path[0]
        i = 2
        
        while i < len(the_path):
            if not self.map.walkable(current, the_path[i]):
                current = the_path[i-1]
                simple_path.append(current)
            i += 1

        simple_path.append(the_path[-1])                
        return simple_path
                
    def find_path(self, simplify=False):
        while len(self.open_set) > 0:
            
            '''find the open node with the lowest cost'''
            current_cost = float('inf')
            current = None            
            for o in self.open_set:
                if current_cost > self.f_score[o]:
                    current_cost = self.f_score[o]
                    current = o
            
            '''return the path found'''        
            if current == self.dest:
                the_path = [current]
                while current in self.came_from:
                    current = self.came_from[current]
                    the_path.append(current)
                the_path.reverse()
                if simplify:
                    return self.simplify(the_path)
                else:
                    return the_path
                
            self.open_set.remove(current)
            self.closed_set.add(current)
            neighbors = self.map.neighbor_tiles(current)
            for n in neighbors:
                if n in self.closed_set:
                    continue
                
                if not self.map.tile_passable(n):
                    continue
                
                tentative_score = self.g_score[current] + self.actual_cost(current, n)
                if n not in self.open_set or tentative_score < self.g_score[n]:
                    self.g_score[n] = tentative_score
                    self.f_score[n] = self.g_score[n] + self.h_cost(n, self.dest)
                    self.came_from[n] = current
                    if not n in self.open_set:
                        self.open_set.add(n)

        return None
                
                    
        
        