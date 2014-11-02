import numpy
import noise
import math
import pickle

class Map(object):
    
    coords = ( (0,-1), (1,0), (0,1), (-1,0), (1,-1), (1,1), (-1,1), (-1,-1), )
    
    def __init__(self, dims, filepath=None):
        assert(len(dims) == 2)
        self.terrain = numpy.zeros(dims, numpy.int)
        self.tiles = numpy.zeros(dims, numpy.int)
        self.size = dims
        
        ndims = (max(dims[0]/15, 1), max(dims[1]/15, 1))
        gen = noise.LayeredNoise2D(ndims, 4, 0.75)
        
        sample = 0.0
        sample_size = 0
        for x in xrange(dims[0]):
            for y in xrange(dims[1]):
                val = gen.val_at( (float(x)/dims[0], float(y)/dims[1]))
                sample += val
                sample_size += 1
                
                if val < 0.35:
                    self.terrain[x][y] = 0
                elif val < 0.45:
                    self.terrain[x][y] = 1
                else:
                    self.terrain[x][y] = 2
                    
        average = sample / sample_size
        print "Average is: "+str(average)        
        self.compute_tiles()

    def save(self, filepath):
        print pickle.dump(self.terrain, open(filepath, "w"))
        
    def load(self, filepath):
        self.terrain = pickle.load( open(filepath, "r"))
        self.compute_tiles()
        
    def compute_tiles(self):
        for x in xrange(self.size[0]):
            for y in xrange(self.size[1]):
                self.set_tile_at((x,y), self.compute_tile((x,y)))
                
    def grow_grass(self):
        neighbors = ((1,0),(-1,0),(0,1),(0,-1))
        dims = self.size
        for x in xrange(dims[0]):
            for y in xrange(dims[1]):
                if self.terrain[x][y] == 2:
                    for c in neighbors:
                        if self.terrain_equal((x+c[0],y+c[1]),0):
                            self.terrain[x][y] = 1
                            print "Converting %d %d to grass" % (x,y)
                            break
                        
        self.compute_tiles()
        
    def get_terrain_at(self, pos):
        return self.terrain[pos[0]][pos[1]]
    
    def set_terrain_at(self, pos, value):
        self.terrain[pos[0]][pos[1]] = value

    def terrain_equal(self, pos, value):
        if pos[0] < 0 or pos[0] >= self.size[0]:
            return False
        elif pos[1] < 0 or pos[1] >= self.size[1]:
            return False
        else:
            return self.get_terrain_at(pos) == value

    def compute_tile(self, pos):
        field = 0        
        coords = self.coords
        for i in xrange(8):
            if self.terrain_equal( (pos[0]+coords[i][0], pos[1]+coords[i][1]), 1):
                field += math.pow(2, i)
        return int(field)
            
    def get_tile_at(self, pos):
        return self.tiles[pos[0]][pos[1]]

    def set_tile_at(self, pos, value):
        self.tiles[pos[0]][pos[1]] = value    