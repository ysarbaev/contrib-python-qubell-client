import unittest2

from qubell.api.private.common import EntityList
from qubell.api.private import exceptions


class EntityListTests(unittest2.TestCase):
    class DummyEntity:
        def __init__(self, id, name):
            self.id = id
            self.name = name

        @property
        def dummy(self):
            'dummy property'
            return self.id + "--==--" + self.name

    class DummyEntityList(EntityList):
        def __init__(self, raw_json):
            self.raw_json = raw_json
            EntityList.__init__(self)

        def _generate_object_list(self):
            self.object_list = [EntityListTests.DummyEntity(item["id"], item["name"]) for item in self.raw_json]

    raw_objects = [
        {"id": "1", "name": "name1"},
        {"id": "2", "name": "name2"},
        {"id": "3", "name": "name3dup"},
        {"id": "4", "name": "name3dup"},
        {"id": "1234567890abcd1234567890", "name": "with_bson_id"}
    ]

    def setUp(self):
        self.entity_list = EntityListTests.DummyEntityList(self.raw_objects)

    def test_get_item_by_name(self):
        assert self.entity_list["name2"].id == "2"

    def test_get_item_by_id(self):
        assert self.entity_list["1234567890abcd1234567890"].name == "with_bson_id"

    def test_get_last_item_when_duplicate_by_name(self):
        assert "4" == self.entity_list["name3dup"].id

    def test_not_existing_item(self):
        with self.assertRaises(exceptions.NotFoundError) as context:
            assert self.entity_list["hren"]
        assert context.exception.message == "None of 'hren' in DummyEntityList"

    def test__len(self):
        assert len(self.raw_objects) == len(self.entity_list)

    def test__in(self):
        dummy = EntityListTests.DummyEntity("1", "name1")
        assert dummy in self.entity_list

    def test__iter(self):
        entity_ids = [e.id for e in self.entity_list]
        raw_ids = [e["id"] for e in self.raw_objects]
        self.assertEqual(entity_ids, raw_ids)
