"""Unit tests for SQLite persistent memory store."""

import tempfile
import unittest
from pathlib import Path
from memory.store import MemoryStore


class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = Path(self.tmp.name)
        self.store = MemoryStore(self.db_path)

    def tearDown(self):
        try:
            self.db_path.unlink()
        except Exception:
            pass

    def test_add_and_get_memory(self):
        mem = self.store.add("Project X", "Launch Mars colony in 2030", tags=["space", "future"])
        self.assertIsNotNone(mem["id"])
        self.assertEqual(mem["title"], "Project X")
        self.assertIn("space", mem["tags"])

        retrieved = self.store.get(mem["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["content"], "Launch Mars colony in 2030")

    def test_list_and_search_memory(self):
        self.store.add("Quantum Note", "Decoherence time is 100 microseconds", tags=["quantum"])
        self.store.add("Grocery List", "Milk, Coffee, Bread", tags=["home"])

        # All memories
        all_mems = self.store.list()
        self.assertEqual(len(all_mems), 2)

        # Keyword search
        search_res = self.store.list(query="Decoherence")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["title"], "Quantum Note")

        # Tag search
        tag_res = self.store.list(tag="home")
        self.assertEqual(len(tag_res), 1)
        self.assertEqual(tag_res[0]["title"], "Grocery List")

    def test_update_and_delete_memory(self):
        mem = self.store.add("Temporary", "To be updated")
        self.assertTrue(self.store.update(mem["id"], title="Updated Title", content="Updated Content"))

        updated = self.store.get(mem["id"])
        self.assertEqual(updated["title"], "Updated Title")
        self.assertEqual(updated["content"], "Updated Content")

        self.assertTrue(self.store.delete(mem["id"]))
        self.assertIsNone(self.store.get(mem["id"]))

    def test_tags_and_seeding(self):
        self.store.add("A", "content", tags=["tag1", "tag2"])
        tags = self.store.get_all_tags()
        self.assertIn("tag1", tags)
        self.assertIn("tag2", tags)


if __name__ == "__main__":
    unittest.main()
