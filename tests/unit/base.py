import unittest
import warnings

from sqlalchemy.exc import LegacyAPIWarning

from app import createApp, db
from app.models import User, Book, Loan, KeyWord, StatusLoan


# Keep test output focused on regressions in project code.
warnings.filterwarnings('ignore', category=LegacyAPIWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning, module=r'flask_session\.sqlalchemy\.sqlalchemy')
warnings.filterwarnings('ignore', message=r'.*datetime\.datetime\.utcnow\(\) is deprecated.*')
warnings.filterwarnings('ignore', message=r'.*Query\.get\(\) method is considered legacy.*')
warnings.filterwarnings('ignore', module=r'flask_sqlalchemy\.query')

_TEST_APP = createApp(config_name="testing")

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """
        Called before each test. Sets up a test client, a test database,
        and the application context.
        """
        self.app = _TEST_APP
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """
        Called after each test. Removes the database session and drops all tables.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_admin_user(self):
        """Helper method to create an admin user for testing protected routes."""
        admin_user = User(
            identificationCode='admin',
            userCompleteName='Administrador',
            password='adminpassword',  # Plain text for test simplicity, will be hashed by model/route
            userType='admin',
            birthDate='1990-01-01',
            createdBy=None,
            updatedBy=None,
        )
        db.session.add(admin_user)
        db.session.commit()
        return admin_user
