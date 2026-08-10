# Shared fixtures live in tests/conftest.py; loading them as a plugin from the
# root makes them available to the app test packages as well.
pytest_plugins = ["tests.conftest"]
