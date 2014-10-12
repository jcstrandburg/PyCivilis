"""Provides base classes for the application framework
"""

import pygame

class Application(object):

    """Application framework base class"""
    
    def __init__(self):
        #fps tracking
        self.fps = 0
        self.fps_bias = .9
        self.set_fps_cap( 50)
        
        #activity stack initialization
        self._activities = [] #stack of activities, only the top is currently active
        self._pending = [] #list of activities waiting to be added to the stack        

        #pygame setup
        pygame.init()
        self.clock = pygame.time.Clock()
        self.clock.tick()        
        self.screen = pygame.display.set_mode((800, 800))
        pygame.mixer.init()        

    def set_fps_cap(self, cap):
        """Sets the maximum framerate (and logic frame time)"""
        self.fps = cap    
        self._max_fps = cap
        self._time_stored = 0.0
        self._logic_frame_time = 1000.0/cap
        self._max_logic_time = 4*self._logic_frame_time
        
    def cleanup(self):
        pygame.quit()
        
    def draw(self):
        """Resets the screen and then tells the top activity to draw"""
        self.screen.fill((200,150,80) )
        top = self._get_top_activity()
        if top is not None:
            top.draw()
        pygame.display.flip()

    def _get_top_activity(self):
        try:
            return self._activities[-1]
        except IndexError:
            return None
        
    def update(self):
        """Handles frame timing and updates the activity stack"""
    
        #add all pending activities to the stack
        if len(self._pending) > 0:
            #pause the top activity
            top = self._get_top_activity()
            if top is not None:
                top.pause()

            #add 'em
            for ActClass, config in self._pending:
                newact = ActClass(self)
                newact.on_create(config)
                self._activities.append(newact)

            #clear the list of pending activities
            del self._pending[:]

        #make sure we have activities to work with
        if len( self._activities) <= 0:
            return False

        #grab the top activity, then kill of this and any other finished activities
        top = self._get_top_activity()
        while top is not None and top.finished:
            top.pause()
            top.on_destroy()
            self._activities.pop()
            top = self._get_top_activity()

        #update fps and update stored time
        ticks = self.clock.tick( self._max_fps)
        self._time_stored = min( self._time_stored+ticks, self._max_logic_time)
        self.fps = self.fps * self.fps_bias + self.clock.get_fps()*(1-self.fps_bias)
        
        if self.fps != float("inf"):
            pygame.display.set_caption( str(round(self.fps))) #this seems to cause a memory leak or something, causing the game to hang on pygame.quit
            
        #if the stack activity isn't empty
        if top is not None:

            #force the top activity to resume and do an update
            top.resume()            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                else:
                    top.handle_event( event)
        
            while self._time_stored > self._logic_frame_time:
                self._time_stored -= self._logic_frame_time
                top.update()

            return True
            
        #else the activity stack is empty
        else:
            return False         
                
    #returns true if the activity stack is empty (does not check pending activities!)
    def activities_empty(self):
        """Returns true if the activity stack is empty"""
        return len(self._activities) == 0
        

    def start_activity(self, ActClass, config=None):
        """Adds the given activity to the stack.
        
        Adds the given activity tot he queue of pending activities,
        to be added to the actual activity stack at the beginning of the
        next call to update.
        """
            #add the given activity to a queue of pending activities to be added at the beginning of the next update
        self._pending.append((ActClass, config))

    def _do_start_activity(self, ActClass, config):
        newact = ActClass(self)
        newact.on_create(config)
        self._activities.append(newact)
        if self._top_activity is not None:
            self._top_activity.pause()

'''Activity base class'''
class Activity(object):

    """Base class for all activities"""

    def __init__(self, controller):
        self.controller = controller
        self.paused = True
        self.finished = False
        self.listeners = []

    def on_create(self, config):
        """Does any initialization work upon activity creation."""
        pass

    def finish(self):
        """End the activity."""
        self.finished = True

    def on_destroy(self):
        """Clean up before removal from the activity stack."""
        pass

    def handle_event(self, event):
        """Handle pygame event."""
        pass

    def resume(self):
        """Resume if paused, otherwise do nothing."""
        if self.paused:
            self.paused = False
            self.on_resume()

    def on_resume(self):
        """Called whenever an activity becomes the top activity on the stack."""
        pass

    def draw(self):
        pass

    def pause(self):
        """Pause if unpaused, otherwise do nothing."""
        if not self.paused:
            self.paused=True
            self.on_pause()

    def on_pause(self):
        """Handle a pause event."""
        pass

    def update(self):
        """Do a logic frame."""
        pass      