import unittest
import os

def run_tests():
    """
    Discover and run all tests in the 'tests/unit' directory.
    """
    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='tests/unit')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if any tests failed
    if not result.wasSuccessful():
        exit(1)

if __name__ == '__main__':
    run_tests()
