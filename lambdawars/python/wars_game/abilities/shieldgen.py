from core.abilities import AbilityBase, AbilityTarget

# Connect to another generator
class AbilityGenConnectInfo(AbilityTarget):
    # Info
    name = 'genconnect'
    image_name = 'vgui/combine/abilities/combine_shield_connect.vmt'
    rechargetime = 0
    displayname = '#CombGenConnect_Name'
    description = '#CombGenConnect_Description'
        
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.player.GetMouseData()
            gen = data.ent
            
            if not gen or not gen.IsUnit() or gen.unitinfo != self.unit.unitinfo or gen == self.unit:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            if gen.powered_1:
                if not gen.powered:
                    self.Cancel(cancelmsg='#Ability_InvalidTarget')
                    return
            if self.unit.powered_1:
                if not self.unit.powered:
                    self.Cancel(cancelmsg='#Ability_InvalidTarget')
                    return
            if not gen.constructionstate is gen.BS_CONSTRUCTED:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
            if not self.unit.constructionstate is self.unit.BS_CONSTRUCTED:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
                
            # Check range
            dist = (self.unit.GetAbsOrigin() - gen.GetAbsOrigin()).Length2D()
            if dist > self.unit.maxgenrange:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
                
            # Connect or destroy
            if self.unit.GetLink(gen):
                self.unit.DestroyLink(self.unit.GetLink(gen))
            else:
                self.unit.CreateLink(gen)


class AbilityGenConnectPoweredInfo(AbilityGenConnectInfo):
    name = 'genconnect_powered'
    
    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        if not unit.powered:
            requirements.add('powered')
        return requirements
        
# Destroy all links of this generator
class AbilityGenDestroyLinks(AbilityBase):
    # Info
    name = "gendestroylinks"
    image_name = 'vgui/combine/abilities/combine_shield_off.vmt'
    rechargetime = 0
    displayname = "#CombGenDestroyLinks_Name"
    description = "#CombGenDestroyLinks_Description"
    hidden = True
    
    # Ability
    def Init(self):
        super().Init()
        
        self.SelectGroupUnits()
        for unit in self.units:
            unit.DestroyAllLinks()
        
    serveronly = True # Do not instantiate on the client