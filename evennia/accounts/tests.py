from mock import Mock
from random import randint
from unittest import TestCase

from evennia.accounts.accounts import AccountSessionHandler
from evennia.accounts.accounts import DefaultAccount
from evennia.server.session import Session
from evennia.utils import create

from django.conf import settings


class TestAccountSessionHandler(TestCase):
    "Check AccountSessionHandler class"

    def setUp(self):
        self.account = create.create_account("TestAccount%s" % randint(0, 999999), email="test@test.com", password="testpassword", typeclass=DefaultAccount)
        self.handler = AccountSessionHandler(self.account)

    def test_get(self):
        "Check get method"
        self.assertEqual(self.handler.get(), [])
        self.assertEqual(self.handler.get(100), [])

        import evennia.server.sessionhandler

        s1 = Session()
        s1.logged_in = True
        s1.uid = self.account.uid
        evennia.server.sessionhandler.SESSIONS[s1.uid] = s1

        s2 = Session()
        s2.logged_in = True
        s2.uid = self.account.uid + 1
        evennia.server.sessionhandler.SESSIONS[s2.uid] = s2

        s3 = Session()
        s3.logged_in = False
        s3.uid = self.account.uid + 2
        evennia.server.sessionhandler.SESSIONS[s3.uid] = s3

        self.assertEqual(self.handler.get(), [s1])
        self.assertEqual(self.handler.get(self.account.uid), [s1])
        self.assertEqual(self.handler.get(self.account.uid + 1), [])

    def test_all(self):
        "Check all method"
        self.assertEqual(self.handler.get(), self.handler.all())

    def test_count(self):
        "Check count method"
        self.assertEqual(self.handler.count(), len(self.handler.get()))

class TestDefaultAccount(TestCase):
    "Check DefaultAccount class"

    def setUp(self):
        self.s1 = Session()
        self.s1.sessid = 0

    def test_puppet_object_no_object(self):
        "Check puppet_object method called with no object param"

        try:
            DefaultAccount().puppet_object(self.s1, None)
            self.fail("Expected error: 'Object not found'")
        except RuntimeError as re:
            self.assertEqual("Object not found", re.message)

    def test_puppet_object_no_session(self):
        "Check puppet_object method called with no session param"

        try:
            DefaultAccount().puppet_object(None, Mock())
            self.fail("Expected error: 'Session not found'")
        except RuntimeError as re:
            self.assertEqual("Session not found", re.message)

    def test_puppet_object_already_puppeting(self):
        "Check puppet_object method called, already puppeting this"

        import evennia.server.sessionhandler

        account = create.create_account("TestAccount%s" % randint(0, 999999), email="test@test.com", password="testpassword", typeclass=DefaultAccount)
        self.s1.uid = account.uid
        evennia.server.sessionhandler.SESSIONS[self.s1.uid] = self.s1

        self.s1.logged_in = True
        self.s1.data_out = Mock(return_value=None)

        obj = Mock()
        self.s1.puppet = obj
        account.puppet_object(self.s1, obj)
        self.s1.data_out.assert_called_with(options=None, text="You are already puppeting this object.")
        self.assertIsNone(obj.at_post_puppet.call_args)

    def test_puppet_object_no_permission(self):
        "Check puppet_object method called, no permission"

        import evennia.server.sessionhandler

        account = create.create_account("TestAccount%s" % randint(0, 999999), email="test@test.com", password="testpassword", typeclass=DefaultAccount)
        self.s1.uid = account.uid
        evennia.server.sessionhandler.SESSIONS[self.s1.uid] = self.s1

        self.s1.puppet = None
        self.s1.logged_in = True
        self.s1.data_out = Mock(return_value=None)

        obj = Mock()
        obj.access = Mock(return_value=False)

        account.puppet_object(self.s1, obj)

        self.assertTrue(self.s1.data_out.call_args[1]['text'].startswith("You don't have permission to puppet"))
        self.assertIsNone(obj.at_post_puppet.call_args)

    def test_puppet_object_joining_other_session(self):
        "Check puppet_object method called, joining other session"

        import evennia.server.sessionhandler

        account = create.create_account("TestAccount%s" % randint(0, 999999), email="test@test.com", password="testpassword", typeclass=DefaultAccount)
        self.s1.uid = account.uid
        evennia.server.sessionhandler.SESSIONS[self.s1.uid] = self.s1

        self.s1.puppet = None
        self.s1.logged_in = True
        self.s1.data_out = Mock(return_value=None)

        obj = Mock()
        obj.access = Mock(return_value=True)
        obj.account = account

        account.puppet_object(self.s1, obj)
        # works because django.conf.settings.MULTISESSION_MODE is not in (1, 3)
        self.assertTrue(self.s1.data_out.call_args[1]['text'].endswith("from another of your sessions."))
        self.assertTrue(obj.at_post_puppet.call_args[1] == {})

    def test_puppet_object_already_puppeted(self):
        "Check puppet_object method called, already puppeted"

        import evennia.server.sessionhandler

        account = create.create_account("TestAccount%s" % randint(0, 999999), email="test@test.com", password="testpassword", typeclass=DefaultAccount)
        self.s1.uid = account.uid
        evennia.server.sessionhandler.SESSIONS[self.s1.uid] = self.s1

        self.s1.puppet = None
        self.s1.logged_in = True
        self.s1.data_out = Mock(return_value=None)

        obj = Mock()
        obj.access = Mock(return_value=True)
        obj.account = Mock()
        obj.at_post_puppet = Mock()

        account.puppet_object(self.s1, obj)
        self.assertTrue(self.s1.data_out.call_args[1]['text'].endswith("is already puppeted by another Account."))
        self.assertIsNone(obj.at_post_puppet.call_args)
