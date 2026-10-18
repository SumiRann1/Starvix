import sys
from pathlib import Path
from unittest.mock import patch

import aiosqlite
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.db import create_db


@pytest.mark.anyio
async def test_create_db(tmp_path):
    test_db_file = tmp_path / "sub" / "test_chatbot.db"
    test_db_file.parent.mkdir(parents=True, exist_ok=True)

    with patch("data.db.DB_PATH", test_db_file):
        await create_db()
        assert test_db_file.exists()

        # Verify table schema
        async with aiosqlite.connect(test_db_file) as db:
            cursor = await db.cursor()
            await cursor.execute("PRAGMA table_info(messages);")
            columns = await cursor.fetchall()
            # columns: [(cid, name, type, notnull, dflt_value, pk), ...]
            col_names = [col[1] for col in columns]
            assert "id" in col_names
            assert "thread_id" in col_names
            assert "model" in col_names
            assert "role" in col_names
            assert "content" in col_names
            assert "timestamp" in col_names
