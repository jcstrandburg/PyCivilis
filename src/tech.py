class Technology(object):
    def __init__(self, tag, reqs, cost):
        self.tag = tag
        self.requirements = reqs
        self.cost = cost
        self.researched = False
        
    def research(self, manager, director):
        self.researched = True
        self.research_handler(manager, director)
        
    def research_handler(self, manager, director):
        pass
    
class TechManager(object):
    def __init__(self):
        self.techs = {}
        self.vars = {}
        self.build_tree()
        
    def tech_available(self, tag):
        tech = self.techs[tag]
        for tag in tech.requirements:
            if not self.is_researched(tag):
                return False
            
        return True

    def available_techs(self):
        
        avails = []
        for tag in self.techs:
            tech = self.techs[tag]
            if not tech.researched and self.tech_available(tag):
                avails.append(tech.tag)
                
        return avails
    
    def is_researched(self, tag):
        tech = self.techs[tag]
        return tech.researched
        
    def research(self, tag, director=None):
        tech = self.techs[tag]
        tech.research(self, director)
        
    def get_tech(self, tag):
        return self.techs[tag]
    
    def add_potential_tech(self, tech):
        self.techs[tech.tag] = tech
        
    def set_var(self, tag, value):
        self.vars[tag] = value
        
    def get_var(self, tag):
        return self.vars[tag]
    
    
class CivilisTechManager(TechManager):
    def build_tree(self):
        techs = (
             Technology('animal_domestication', (), 100),
             Technology('animal_husbandry', ('animal_domestication',), 200),
             Technology('patriarchy', (), 100),
             Technology('specialized_labor', ('patriarchy','advanced_tools'), 200),
             Technology('writing', ('specialized_labor',), 300),
             Technology('trade', ('specialized_labor',), 300),
             Technology('organized_religion', ('writing',), 350),
             Technology('kingship', ('organized_religion',), 400),
             Technology('advanced_tools', (), 100),
             Technology('basic_farming', ('advanced_tools',), 200),
             Technology('advanced_farming', ('basic_farming',), 300),
             Technology('metalworking', ('advanced_tools',), 200),
             Technology('basic_weapons', (), 100),
             Technology('advanced_weapons', ('basic_weapons','metalworking'), 200),
         )

        for tech in techs:
            self.add_potential_tech(tech)
        
        self.set_var('base_work_rate', 1.0)
        self.set_var('stone_work_rate', 3.0)
        self.set_var('wood_work_rate', 0.5)
        self.set_var('pottery_work_rate', 2.0)        
        
        self.set_var('hunt_work_rate', 1.0)
        self.set_var('butcher_work_rate', 1.0)
        
        
        