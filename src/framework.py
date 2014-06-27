"""
Justin Strandburg
Civilis

Application framework
"""

import pygame
import random, time, os, fnmatch, sys

from animation import AnimatedImage

class ResourceManager(object):

    def __init__(self):
        self._resources = {} #dictionary of actual resource objects, indexed by uri's
        self._preloads = {} #dictionary of resource uri's and 
        self._dirpath = None        
        pass

    def force_reload(self):
        self._resources = {}
        
    def load(self, dirpath, listpath):
        self._dir = dirpath

        f = file(os.path.join(dirpath, listpath), 'r')
        for line in f:
            line = line.strip()
            if (len(line) > 0 and line[0] != '#' ):
                restype, tag, path  = line.split(',')
                restype, tag, path = restype.strip(), tag.strip(), path.strip()
                self._preloads[tag] = (restype, os.path.join(dirpath, path))

    def get(self, tag):
        try:
            #get the uri
            restype, uri = self._preloads[tag]

            #try to grab it..
            try:
                return self._resources[ uri]

            #it's not loaded yet, try to load it
            except KeyError:
                if restype == "image":
                    self._resources[uri] = pygame.image.load(uri).convert_alpha()
                elif restype == "sound":
                    self._resources[uri] = pygame.mixer.Sound(uri)
                elif restype == "anim":
                    self._resources[uri] = AnimatedImage(uri)
                else:
                    raise Exception("Unkown resource type "+restype+" on resource "+tag)                    
                    return None

                return self._resources[uri]

        except KeyError:
            raise Exception("Request for unkown resource " + tag)


class SettingsManager(object):

    def __init__(self):
        self._settings = {}
    
    def load(self, filepath):
        f = file(filepath, 'r')
        for line in f:
            line = line.strip()
            if (len(line) > 0 and line[0] != '#' ):
                tag, string_value = line.split('=')
                tag = tag.strip()
                string_value = string_value.strip()
                
                try:
                    value = int(string_value)
                except:
                    try:
                        value = float(string_value)
                    except:
                        value = string_value
                self.put(tag, value)

    def get(self, tag, default=None):
        try:
            return self._settings[tag]
        except KeyError:
            return default

    def put(self, tag, value):
        self._settings[tag] = value

    def dump(self):
        for key in self._settings:
            val = self._settings[key]
            print key, type(val), val

class GameController(object):
    
    def __init__(self):
        self.fps = 0
        self.fps_bias = .7
        pass

    def startup(self):

        pygame.init()

        self._activities = [] #stack of activities, only the top is currently active
        self._pending = [] #list of activities waiting to be added to the stack
        self._time_stored = 0.0 #the amount of time that needs to be simulated in state changes
        
        settings.load('config.txt')
        resources.load(settings.get("res_dir", "res"),
                             settings.get("res_list", "resources.txt"))
        self.level_dir = settings.get("level_dir", "lev")

        w = settings.get("screenw", 400)
        h = settings.get("screenh", 400)
        self._min_timestep = settings.get("min_timestep", "0.005")#the lowest amount of time that can occur in a state update
        self._max_timestep = settings.get("max_timestep", "0.1")#the max time that can occure in a state update
        self._max_steps = settings.get("max_steps_per_frame", 10)#maximum number of state updates performed per frame drawn (for low fps situations)

        self.screen = pygame.display.set_mode((w, h))
        pygame.mixer.init()

        self.clock = pygame.time.Clock()
        self.clock.tick()

    def level_path(self, level):
        level = str(level)+".xml"
        return os.path.join( self.level_dir, level)
 
    def cleanup(self):
        print "calling pygame.quit"
        pygame.quit()
        print "done, calling sys.exit"
        sys.exit()
        
    def get_level_list(self):
        files = os.listdir("levels")
        names = []
        for x in files:
            if fnmatch.fnmatch( x, "*.xml"):
                try:
                    base = int( os.path.splitext( x)[0])
                    names.append( base)
                except ValueError:#just ignore filenames that aren't numbers
                    pass
        names.sort()
        return names

    def draw(self):
        self.screen.fill((0,0,0) )
        top = self._top_activity()
        if top is not None:
            top.draw(self.screen)
        pygame.display.flip()

    def _top_activity(self):
        if len(self._activities) > 0:
            return self._activities[-1]
        else:
            return None        
        
    def handle_event(self, event):
        top = self._top_activity()
        if top is not None:
            top.handle_event(event)

    def update(self, timestep = None):

        #add all pending activities to the stack
        if len(self._pending) > 0:

            #pause the top activity
            top = self._top_activity()
            if top is not None:
                top.pause()

            #add em
            for ActClass, config in self._pending:
                newact = ActClass(self)
                newact.on_create(config)
                self._activities.append(newact)

            #clear the list of pending activities
            del self._pending[:]

        #make sure we have activities to work with
        if self.activities_empty():
            return None

        #grab the top activity, then kill of this and any other finished activities
        top = self._top_activity()
        while top is not None and top.finished:
            top.pause()
            top.on_destroy()
            self._activities.pop()
            top = self._top_activity()

        #calculate the timestep if none provided
        if timestep is None:   
            ticks = self.clock.tick()
            timestep = float(ticks)/1000
            self._time_stored += timestep

        self.fps = self.fps * self.fps_bias + self.clock.get_fps()*(1-self.fps_bias)
        #pygame.display.set_caption( str(int(self.fps))) #this seems to cause a memory leak or something, causing the game to hange on pygame.quit
            
        #force the top activity to resume and do an update
        if top is not None:
            top.resume()

            for i in range(self._max_steps):
                if self._time_stored > self._min_timestep:
                    timestep = min((self._time_stored, self._max_timestep))
                    top.update(timestep)
                    self._time_stored -= timestep
                
    #returns true if the activity stack is empty (does not check pending activities!)
    def activities_empty(self):
        return len(self._activities) == 0
        

    #add the given activity to a queue of pending activities to be added at the beginning of the next update
    def start_activity(self, ActClass, config):
        self._pending.append((ActClass, config))

    def _do_start_activity(self, ActClass, config):
        newact = ActClass(self)
        newact.on_create(config)
        self._activities.append(newact)
        if self._top_activity is not None:
            self._top_activity.pause()

class Activity(object):

    def __init__(self, controller):
        self.controller = controller
        self.paused = 1
        self.finished = 0
        self.listeners = []

    def on_create(self, config):
        pass

    def finish(self):
        self.finished = 1

    def on_destroy(self):
        pass

    def handle_event(self, event):
        pass

    def resume(self):
        if self.paused:
            self.paused = 0
            self.on_resume()

    def on_resume(self):
        pass

    def draw(self, screen):
        pass

    def pause(self):
        if not self.paused:
            self.paused=1
            self.on_pause()

    def on_pause(self):
        pass

    def update(self, timestep):
        pass


settings = SettingsManager()
resources = ResourceManager()
