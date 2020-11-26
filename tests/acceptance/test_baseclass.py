"""
base class for pytest

alchemist

"""

import unittest
# import sh
from app import application


class TestBase(unittest.TestCase):
    """
    Test Base
    """
    def setUp(self):
        """
        start application test client,
        This function runs once before each member function unit test.
        """
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False
        self.app = application.test_client()
        self.app_context = application.app_context()
        self.app_context.push()

    def tearDown(self):
        """
        somethin to restore
        like reset db if necessary
        """
        self.app_context.pop()
