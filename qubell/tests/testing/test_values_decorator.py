import unittest

from qubell.api.private.testing import values


__author__ = 'dmakhno'

# noinspection PyUnresolvedReferences
class ValuesDecoratorTests(unittest.TestCase):
    class FakeInstance(object):
        def __init__(self, return_value):
            self.returnValues = return_value

    rv = {"str": "some string", "empty-str": '', "none": None, "i": 10, "f": 2.3, "b": True,
          "complex": {"complex-val": "some value", "complex-list-single": ["single"],
                      "complex-list-multi": ["l1", "l2", "l3"]}}
    mapping = {"str": "str", "complex-val": "some_val", "complex-list-single": "single", "complex-list-multi": "multi",
               "complex": "complex", "empty-str": "empty", "none": "none", "i": "i", "f": "f", "b": "b"}
    instace = FakeInstance(rv)

    @values(mapping)
    def decorated_method(self, instance, str=None, complex=None, some_val=None, single=None, multi=None, empty=False,
                         none=False, i=None, f=None, b=None, callback=None):
        callback.str = str
        callback.complex = complex
        callback.some_val = some_val
        callback.single = single
        callback.multi = multi
        callback.empty = empty
        callback.none = none
        callback.i = i
        callback.f = f
        callback.b = b

    def setUp(self):
        class dummy(object): pass

        self.obj = dummy()
        self.decorated_method(instance=self.instace, callback=self.obj)

    def test_json_string(self):
        assert self.obj.str == "some string"

    def test_json_empty(self):
        assert self.obj.empty == ''

    def test_json_none(self):
        assert self.obj.none == None

    def test_json_bool(self):
        assert self.obj.b == True

    def test_json_int(self):
        assert self.obj.i == 10

    def test_json_float(self):
        assert self.obj.f == 2.3

    def test_json_inside(self):
        assert self.obj.some_val == "some value"

    def test_list_with_one_element(self):
        assert self.obj.single == "single"

    def test_list_with_many_elemetns(self):
        self.assertEqual(self.obj.multi, self.rv['complex']['complex-list-multi'])

    def test_string(self):
        self.assertEqual(self.obj.complex, self.rv['complex'])

    @values({"x-name": "x", "y-name": "y"})
    def missing_params_method(self, instance, a, b): pass

    def test_missing_params(self):
        with self.assertRaises(AttributeError) as context:
            self.missing_params_method(instance=self.instace)
        self.assertItemsEqual(context.exception.args[1], ["x-name", "y-name"])

    @values({"empty-str": "empty"})
    def exceeded_params_methos(self, instance): pass

    def test_exceeded_params(self):
        with self.assertRaises(TypeError) as context:
            self.exceeded_params_methos(instance=self.instace)