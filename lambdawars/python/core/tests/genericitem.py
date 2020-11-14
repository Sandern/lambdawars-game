from unittest import TestSuite
from unittest.util import strclass
from srctests.gametestcase import GenericGameTestCase
from srctests.gametestsuite import GameTestSuite

from ..ents.genericitem import GenericItem

def CreateGenericItemTestSuite():
    suite = GameTestSuite()
    suite.addTest(GenericGameGenericItemTestCase())
    return suite
    
class GenericGameGenericItemTestCase(GenericGameTestCase):
    def setUp(self):
        super().setUp()
        
        self.worldmodelname = "models/pg_props/pg_obj/pg_item_satellite.mdl"
        self.carrymodelname = "models/pg_props/pg_obj/pg_backpack_satellite.mdl"

        self.testsleft = [
            (self.testSpawnGenericItem, []),
        ]

    def testSpawnGenericItem(self):
        ent_item = self.CreateAndSpawnEntity('wars_generic_item', {
            "classname" : "wars_generic_item",
            "AfterDropPickupableDelay" : "0.000000",
            "afterdroppickupdelay" : "1.000000",
            "angles" : "0 39.5 0",
            "bonemerge" : "1",
            "carrymodel" : self.carrymodelname,
            "disablereceiveshadows" : "0",
            "disableshadows" : "0",
            "EnabledForPickup" : "1",
            "enableforpickup" : "1",
            "health" : "0",
            "model" : self.worldmodelname,
            "ownernumber" : "0",
            #"pickupfilter" : "item_filter_owner",
            "renderamt" : "255",
            "rendercolor" : "255 255 255",
            "renderfx" : "0",
            "rendermode" : "0",
            "resettime" : "0.000000",
            "skin" : "0",
            "targetname" : "zombie_antena_part",
            "unittype" : "unit_unknown",
        }, activate=True)
        
        self.assertIsNotNone(ent_item, msg='Failed to spawn generic item')
        
        self.assertTrue(ent_item.GetModelName() == self.worldmodelname, msg='Expecting model name %s, instead found %s' % (self.worldmodelname, ent_item.GetModelName()))