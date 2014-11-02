import numpy
import math

def cos_interpolate(a, b, x):
    angle = x * math.pi
    x = (1-math.cos(angle)) * 0.5
    return a*(1-x) + b*x
    

class Noise1D(object):
    
    def __init__(self, resolution):
        self.resolution = resolution
        self.seeds = numpy.random.random(resolution+1)
        
    def val_at(self, pos):
        index = numpy.clip(pos * self.resolution, 0, self.resolution)
        
        return cos_interpolate(self.seeds[math.floor(index)], self.seeds[math.ceil(index)], index-math.floor(index))
        
class Noise2D(object):

    def __init__(self, resolution):
        self.resolution = resolution
        self.seeds = numpy.random.random((resolution[0]+1,resolution[1]+1))
        
    def val_at(self, pos):
    
        pos = (pos[0] % 1.0, pos[1] % 1.0)
    
        index1 = numpy.clip(pos[0] * self.resolution[0], 0, self.resolution[0])#x index
        index2 = numpy.clip(pos[1] * self.resolution[1], 0, self.resolution[1])#y index
        
        a = cos_interpolate(self.seeds[math.floor(index1)][math.floor(index2)], self.seeds[math.ceil(index1)][math.floor(index2)], index1-math.floor(index1))
        b = cos_interpolate(self.seeds[math.floor(index1)][math.ceil(index2)], self.seeds[math.ceil(index1)][math.ceil(index2)], index1-math.floor(index1))
    
        return cos_interpolate(a, b, index2-math.floor(index2))
    
class LayeredNoise2D(object):

    def __init__(self, resolution, layers, falloff):
        self.noise = [Noise2D((resolution[0]*math.pow(2,f), resolution[1]*math.pow(2,f))) for f in xrange(layers)]
        self.layers = layers
        self.falloff = falloff
        self.factor = sum([math.pow(falloff,i) for i in xrange(layers)])
        print self.factor
        
    def val_at(self, pos):
        total = 0
        for i in xrange(self.layers):
            total += self.noise[i].val_at( (pos[0], pos[1])) * math.pow(self.falloff, i)
            
        return total / self.factor