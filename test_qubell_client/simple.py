

from stories import base
from stories.base import attr


class FirstTest(base.BaseTestCasePrivate):

    def test_instane_launch(self):
        app = self.organization.application(manifest=self.manifest)
        self.assertTrue(app.name) # we can get False if error

        instance = app.launch()
        self.assertTrue(instance)         # Instance launch will return False if errors
        self.assertTrue(instance.ready()) # Wait until instance become running

        self.assertFalse(app.delete())    # Can't delete app if it has running instance. check it
        self.assertTrue(instance.destroy())
        self.assertTrue(instance.destroyed())
        self.assertTrue(app.delete())
