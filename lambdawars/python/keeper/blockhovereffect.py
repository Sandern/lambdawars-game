
if isclient:
    from vmath import Vector, QAngle, VectorAngles
    from vgui.controls import Panel
    from vgui import surface, WarsVGUIScreen
    from te import ClientSideEffect
    from entities import C_HL2WarsPlayer

    class BlockSelectionPanel(Panel):
        def Paint(self):
            # draw the outline of the healthbar
            surface().DrawSetColor(0, 255, 0, 255)
            surface().DrawOutlinedRect(
                0, 
                0, 
                self.GetWide(), 
                self.GetTall() 
            )
            
    blockselectionpanel = BlockSelectionPanel()
    
    class BlockSelectionRenderer(ClientSideEffect):
        def __init__(self):
            super().__init__('BlockSelectionRenderer')
            self.screen = None
            
        def Draw(self, frametime):
            if not self.IsActive():
                return
            if self.screen:
                self.screen.Draw()
        
    class BlockScreen(WarsVGUIScreen):
        def __init__(self, block):
            super().__init__()
            
            assert(block != None)

            self.SetPanel(blockselectionpanel)

            self.renderer = block.owner.blockselectioneffect
            self.renderer.screen = self
            
            self.block = block
            
            self.GetPanel().SetBounds(0, 0, 64, 64)
            
        def Shutdown(self):
            self.renderer.screen = None
            self.SetPanel(None)
        
        def Draw(self):
            player = C_HL2WarsPlayer.GetLocalPlayer()
            if not player:
                return
                
            block = self.block
            if not block:
                return
            
            mins = block.mins
            maxs = block.maxs
        
            wide = maxs.x - mins.x
            tall = maxs.y - mins.y
            self.SetWorldSize(wide, tall)
            
            origin = Vector(block.GetAbsOrigin())
            origin.x += self.block.owner.xsize / 2.0
            origin.y -= self.block.owner.ysize / 2.0
            origin.z += block.maxs.z + 6.0
            self.SetOrigin( origin )
            
            angles = QAngle()
            dir = Vector(0,1,0) # Always point up
            VectorAngles(dir, angles)
            self.SetAngles(angles)
        
            super().Draw()