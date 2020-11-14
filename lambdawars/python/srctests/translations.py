from unittest import TestSuite, TestCase
import glob
from kvdict import LoadFileIntoDictionaries

def CreateTranslationsTestSuite():
    suite = TestSuite()
    for path in glob.glob('resource/lambdawars_ui_*.txt'):
        suite.addTest(TranslationsTestCase('test_loadtranslations', path))
        suite.addTest(TranslationsTestCase('test_missingkeys', path))
    return suite

class TranslationsTestCase(TestCase):
    """ Test functions related to translations """
    def __init__(self, testMethod, transPath):
        super().__init__(testMethod)
        
        self.transPath = transPath
    
    def setUp(self):
        pass
        
    def __str__(self):
        return '%s => %s' % (super().__str__(), self.transPath)
        
    def test_loadtranslations(self):
        """ Test if translations can be loaded and if valid. """
        path = self.transPath
        
        # TODO: Will only give a console warning if loading failed.
        #       However the second check and test_missingkeys will probably bug out already if this happens...
        translations = LoadFileIntoDictionaries(path, default=None)
        self.assertTrue(translations != None)
        
        with open(path, 'r', encoding='utf-8') as fp:
            for i, line in enumerate(fp.readlines()):
                # To check: Could be multi-line?
                self.assertTrue(line.count('"') % 2 == 0, msg='line %d "%s" has missing double quotes' % (i, line))

    def test_missingkeys(self):
        """ Test if all translation files have no missing keys compared to the english base translation file. """
        path = self.transPath

        basetranskeys = self.get_translation_keys('resource/lambdawars_ui_english.txt')
    
        transkeys = self.get_translation_keys(path)
        missingkeys = basetranskeys - transkeys 
        removedkeys = transkeys - basetranskeys
        self.assertTrue(len(missingkeys) == 0, msg='Translation file "%s" has missing keys: %s' % (path, ', '.join(missingkeys)))
        self.assertTrue(len(removedkeys) == 0, msg='Translation file "%s" has unused keys: %s' % (path, ', '.join(removedkeys)))

    def get_translation_keys(self, path):
        return set(LoadFileIntoDictionaries(path, default={})['Tokens'].keys())
