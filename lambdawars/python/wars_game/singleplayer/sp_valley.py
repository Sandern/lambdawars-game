#contains special versions of buildigns and units for sp_valley
from wars_game.buildings.rebels.barracks import RebelBarInfo
from wars_game.units.rebel import RebelInfo, RebelPartisanInfo

class RebelBarSpValleyInfo(RebelBarInfo):
    name = "sp_valley_build_reb_barracks"
    abilities = {
        1: 'sp_valley_unit_rebel_partisan',
        2: 'sp_valley_unit_rebel',
        11: 'cancel',
    } 

class RebelPartisanSpValleyInfo(RebelPartisanInfo):
    name = 'sp_valley_unit_rebel_partisan'
    techrequirements = []
    costs = [[('requisition', 10)], [('kills', 1)]]

    
class RebelSpValleyInfo(RebelInfo):
    name = 'sp_valley_unit_rebel'
    techrequirements = []
    costs = [[('requisition', 30)], [('kills', 1)]]