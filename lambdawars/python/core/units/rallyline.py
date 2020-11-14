''' Defines the rally line class, used for displaying lines between orders. 
'''

from srcbase import Color
from vmath import Vector, VectorNormalize, DotProduct, CrossProduct
from te import ClientSideEffect, MeshBuilder, MeshRallyLine, MATERIAL_QUADS, MeshVertex
import ndebugoverlay

class FXRallyLine(ClientSideEffect):
    def __init__(self, material, color, point1, point2, ent1=None, ent2=None):
        super().__init__('FXQuad')
        
        self.material = material
        self.color = color
        self.point1 = point1
        self.point2 = point2
        self.ent1 = ent1
        self.ent2 = ent2
        
        self.texturex = 64.0
        self.texturey = 192.0
        
        self.CreateLine()
        
    def VectorToColor(self, v):
        return Color(int(v.x*255), int(v.y*255), int(v.z*255), 255)
        
    def CreateLine(self):
        flSize = 8.0
        mesh = None
        
        if self.ent1 or self.ent2:
            mesh = MeshRallyLine(self.material)
            
            if self.ent1:
                mesh.ent1 = self.ent1
            elif self.point1:
                mesh.point1 = self.point1

            if self.ent2:
                mesh.ent2 = self.ent2
            elif self.point2:
                mesh.point2 = self.point2

            mesh.color = self.VectorToColor(self.color)
            mesh.texturex = self.texturex
            mesh.texturey = self.texturey
            mesh.size = flSize
            mesh.textureyscale = self.texturex/(flSize*2)
            #mesh.texturexscale = flSize * 2
            
            mesh.Init()
        elif self.point1 and self.point2:
            point1 = self.point1
            point2 = self.point2

            dir = point1 - point2
            VectorNormalize(dir)
            
            vRight = CrossProduct(dir, Vector(0, 0, 1))
            VectorNormalize(vRight)
            
            scale = self.texturex/(flSize*2)
        
            mesh = MeshBuilder(self.material, MATERIAL_QUADS)
            
            vertex1 = MeshVertex()
            vertex1.position = (point1 + (vRight * flSize))
            vertex1.color = self.VectorToColor(self.color)
            
            vertex2 = MeshVertex()
            vertex2.position = (point2 + (vRight * flSize))
            vertex2.color = self.VectorToColor(self.color)
            
            vertex3 = MeshVertex()
            vertex3.position = (point2 + (vRight * -flSize))
            vertex3.color = self.VectorToColor(self.color)
            
            vertex4 = MeshVertex()
            vertex4.position = (point1 + (vRight * -flSize))
            vertex4.color = self.VectorToColor(self.color)
        
            #ndebugoverlay.Line(vertex1.position, vertex2.position, 0, 255, 0, True, 5.0)
            #ndebugoverlay.Line(vertex2.position, vertex3.position, 0, 255, 0, True, 5.0)
            #ndebugoverlay.Line(vertex3.position, vertex4.position, 0, 255, 0, True, 5.0)
            #ndebugoverlay.Line(vertex4.position, vertex1.position, 0, 255, 0, True, 5.0)
            
            linelength = (point1 - point2).Length()
            
            vertex2.s = round(linelength / (self.texturey/scale))
            vertex2.t = 0.0
            vertex3.s = round(linelength / (self.texturey/scale))
            vertex3.t = 1.0
            vertex4.s = 0.0
            vertex4.t = 1.0
            
            mesh.AddVertex(vertex1)
            mesh.AddVertex(vertex2)
            mesh.AddVertex(vertex3)
            mesh.AddVertex(vertex4)
        
        if mesh:
            self.AddMeshBuilder(mesh)
    
