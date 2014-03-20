import unittest

from qubell.api.tools import retry


class RetryTest(unittest.TestCase):
    def setUp(self):
        class Counter(object):
            i = 0

        self.counter = Counter()

    def test_bypass_return_with_only_try(self):
        @retry(1, 0, 0)
        def return_smth():
            self.counter.i += 1
            return "something"

        self.assertEqual(return_smth(), "something")
        self.assertEqual(self.counter.i, 1)

    def test_bypass_return(self):
        @retry(3, 0, 0, Exception)
        def return_smth():
            self.counter.i += 1
            return "something"

        self.assertEqual(return_smth(), "something")
        self.assertEqual(self.counter.i, 1)

    def test_false_without_exceptions_is_retry_indicator(self):
        @retry(3, 0, 0)
        def return_false():
            self.counter.i += 1
            return False

        self.assertEqual(return_false(), False)
        self.assertEqual(self.counter.i, 3)

    def test_true_without_exceptions_is_stop_indicator(self):
        @retry(5, 0, 0)
        def return_false():
            self.counter.i += 1
            if self.counter.i < 3:
                return False
            return True

        self.assertEqual(return_false(), True)
        self.assertEqual(self.counter.i, 3)

    def test_retry_on_unknown_exception(self):
        @retry(5, 0, 0, AssertionError)
        def return_good():
            self.counter.i += 1
            if self.counter.i < 3:
                assert False
            return "good"

        self.assertEqual(return_good(), "good")
        self.assertEqual(self.counter.i, 3)

    def test_fail_on_unexpected_exception(self):
        @retry(5, 0, 0, TypeError)
        def return_smth():
            self.counter.i += 1
            if self.counter.i < 3:
                raise ArithmeticError("boom")
            return "good"

        with self.assertRaises(ArithmeticError):
            return_smth()
        self.assertEqual(self.counter.i, 1)

    def test_bypass_return_after_catching(self):
        @retry(5, 0, 0, AssertionError)
        def return_good():
            self.counter.i += 1
            if self.counter.i < 3:
                assert False
            return "good"

        self.assertEqual(return_good(), "good")

    def test_fail_on_exception_for_non_cathching_mode(self):
        @retry(5, 0, 0)
        def return_exception():
            self.counter.i += 1
            raise ArithmeticError("boom")

        with self.assertRaises(ArithmeticError):
            return_exception()
        self.assertEqual(self.counter.i, 1)

    def test_propagate_known_exception_on_retries_out(self):
        @retry(5, 0, 0, ArithmeticError)
        def return_smth():
            self.counter.i += 1
            raise ArithmeticError("boom")

        with self.assertRaises(ArithmeticError):
            return_smth()
        self.assertEqual(self.counter.i, 6)

    def test_propagate_known_exceptions_on_retries_out(self):

        @retry(5, 0, 0, (ArithmeticError, TypeError))
        def return_smth():
            self.counter.i += 1
            if self.counter.i % 2 == 0:
                raise TypeError("boom_even")
            raise ArithmeticError("boom_odd")

        with self.assertRaises(TypeError):
            return_smth()
        self.assertEqual(self.counter.i, 6)