from entities import CPointEntity, entity
from fields import PlayerField, IntegerField, BooleanField, input
from playermgr import relationships, Disposition_t

dispositionchoices = [
    (Disposition_t.D_HATE, 'Hate'),
    (Disposition_t.D_FEAR, 'Fear'),
    (Disposition_t.D_LIKE, 'Like'),
    (Disposition_t.D_NEUTRAL, 'Neutral'),
]

@entity('wars_player_relation',
        base=['Targetname', 'Parentname', 'Angles'],
        iconsprite='editor/wars_player_relation.vmt')
class EntPlayerRelation(CPointEntity):
    @input(inputname='ApplyRelation', helpstring='')
    def InputApplyRelation(self, inputdata):
        key = (self.subjectplayer, self.targetplayer)
        disposition = Disposition_t(self.disposition)
        relationships[key] = disposition
        if self.reciprocal:
            key2 = (self.targetplayer, self.subjectplayer)
            relationships[key2] = disposition
        
    subjectplayer = PlayerField(keyname='subjectplayer', displayname='Player Subject', helpstring='Subject to which the relation is applied' )
    targetplayer = PlayerField(keyname='targetplayer', displayname='Player Target', helpstring='Target of the applied relation')
    disposition = IntegerField(value=Disposition_t.D_LIKE, keyname='Disposition', displayname='Disposition', choices=dispositionchoices, helpstring='Relation to be applied.')
    reciprocal = BooleanField(value=False, keyname='reciprocal', displayname='Reciprocal', helpstring='Applies the relation to both sides (not just to the subject')