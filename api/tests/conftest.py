"""Provide dummy required env vars before any `app.*` import happens.

Settings() is instantiated eagerly at import time (app/config.py), and
app/services/__init__.py eagerly imports every service — so importing even a
single dependency-free module like app.services.nutrition_calculator pulls in
the whole settings chain. Pytest loads conftest.py before collecting test
modules, so this runs first regardless of test file import order.
"""

import base64
import os

os.environ.setdefault("SUPABASE_DB_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")
os.environ.setdefault("API_KEY_ENCRYPTION_SECRET", base64.b64encode(b"0" * 32).decode())
