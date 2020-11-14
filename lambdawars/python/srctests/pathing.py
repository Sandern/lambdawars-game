from . gametestsuite import GameTestSuite
from . gametestcase import GenericGameTestCase
from vmath import vec3_origin, Vector
from navmesh import NavMeshGetPathDistance

def CreatePathingTestSuite():
    suite = GameTestSuite()
    suite.addTest(PathingTestCase())
    return suite

class PathingTestCase(GenericGameTestCase):
    def runTest(self):
        dist = NavMeshGetPathDistance(vec3_origin, Vector(512, 0, 0))
        expdist = 512.0
        self.assertTrue(abs(dist - expdist) < 4.0, msg='dist is %f, expected within %f' % (dist, expdist))

        dist = NavMeshGetPathDistance(Vector(-768, 256, 0), Vector(-512, 256, 0))
        expdist = 256.0
        self.assertTrue(abs(dist - expdist) < 4.0, msg='dist is %f, expected within %f' % (dist, expdist))

        identical = Vector(-512, 512, 0)
        expdist = 0.0
        dist = NavMeshGetPathDistance(identical, identical)
        self.assertTrue(abs(dist - expdist) < 10.0, msg='Expected distance for same points to similar, but found %f instead' % dist)

