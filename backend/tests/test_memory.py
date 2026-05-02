import unittest

from memory import add_message


class MemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_message_rejects_invalid_role_before_db_write(self):
        with self.assertRaises(ValueError):
            await add_message(
                db=None,
                conversation_id="conversation-id",
                role="system",
                content="Should not be persisted.",
            )


if __name__ == "__main__":
    unittest.main()
