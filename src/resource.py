
class Prototype(object):
    def __init__(self, tag, sprite=None):
        self.parent = None
        self.tag = tag
        self.children = {}
        self.sprite = sprite
        pass
        
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

def show_tree(base, depth=0):
    output = ""
    for i in xrange(depth):
        output += '  '
    output += '-'
    output += base.tag
    print output
    for key in base.children:
        show_tree(base.children[key], depth+1)