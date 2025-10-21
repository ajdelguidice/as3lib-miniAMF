from miniamf.tests import util
from importlib.util import find_spec


# This was removed in "Gen 2" appengine. I'm not sure if there is an
# equivalent or if this is even required anymore.
#try:
#    import dev_appserver

#    dev_appserver.fix_sys_path()
#except ImportError:
#    dev_appserver = None


class BaseTestCase(util.ClassCacheClearingTestCase):
    """
    A base test class for all Google AppEngine related tests. Inits the testbed
    and tears it down once the test is finished.
    """

    # list of stubs to be activated for this test suite
    # see https://cloud.google.com/appengine/docs/python/tools/localunittesting
    # for all available stubs
    testbed_stubs = [
        'datastore_v3',
        'memcache',
        'blobstore',
    ]

    def setUp(self):
        if not has_appengine_sdk():
            self.skipTest('google appengine sdk not found')

        from google.appengine.ext import testbed

        util.ClassCacheClearingTestCase.setUp(self)

        self.testbed = testbed.Testbed()

        self.testbed.activate()

        # Next, declare which service stubs you want to use.
        for stub in self.testbed_stubs:
            func = getattr(self.testbed, 'init_%s_stub' % (stub,))

            func()

        self.addCleanup(self.testbed.deactivate)


def has_appengine_sdk():
    """
    Whether or not the Google AppEnging SDK is bootstrapped.
    """
    return find_spec('google.appengine') is not None
