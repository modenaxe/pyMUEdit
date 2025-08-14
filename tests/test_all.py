import unittest

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("tests", pattern="Test*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
