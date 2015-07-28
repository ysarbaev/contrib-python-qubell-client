import logging


class SetupOnce(object):
    """
    Trait for unittest.TestCase
    Allows do not use test class methods, such as setUpClass or tearDownClass.

    This allows to avoid failed suites. And always each test has failed.
    """

    __counter = 0

    setup_error = None

    def setup_once(self):
        """
        Hook method for setting up fixture before running tests.
        Has instance scope.
        """

    def teardown_once(self):
        """
        Hook method for deconstructing the test fixture after testing it.
        Has instance scope.
        """

    # todo: fixme
    def addcleanup_once(self, function, *args, **kwargs):
        """
        Add a function, with arguments, to be called when the test is
        completed. Functions added are called on a LIFO basis and are
        called after tearDown on test failure or success.

        Should be used only within setup_once or teardown_once scopes.

        If setUp() fails, meaning that tearDown() is not called,
        then any cleanup functions added will still be called.
        """
        if self.__counter == 1:  # counter already increased by one
            self.addCleanUp(function, *args, **kwargs)

    def setUp(self):
        super(SetupOnce, self).setUp()
        logging.info(self.__counter)
        if self.__counter == 0:
            self.__counter += 1
            try:
                self.setup_once()
            except BaseException as e:
                import sys
                self.setup_error = sys.exc_info()

        if self.setup_error:
            raise self.setup_error[1], None, self.setup_error[2]



    def tearDown(self):


        if self.__counter > 1:
            self.__counter -= 1
        else:
            self.teardown_once()
        super(SetupOnce, self).tearDown()