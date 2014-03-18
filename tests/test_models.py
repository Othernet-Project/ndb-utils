from google.appengine.ext import ndb

import formencode
from formencode import validators
import mock

from ndb_utils.models import *

from dbunit import DatastoreTestCase


class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()


class TestModel(RandomMixin, ndb.Model):
    pass


class TestOwnerModel(OwnershipMixin, ndb.Model):
    pass


class TestValidationModel(ValidatingMixin, ndb.Model):
    email = ndb.StringProperty()

    validate_schema = {
        'email': validators.Email()
    }


class TestAncestryParentModel(ndb.Model):
    foo = ndb.StringProperty()


class TestAncestryModel(UniqueByAncestryMixin, ndb.Model):
    bar = ndb.StringProperty()

    ancestry_path = ['TestAncestryParentModel']


class TestUniqueModel(UniquePropertyMixin, ndb.Model):
    foo = ndb.StringProperty()
    bar = ndb.StringProperty()

    unique_properties = ['foo']


class RandomMixinTestCase(DatastoreTestCase):
    """ Tests for RandomMixin """

    def test_random_id(self):
        """ Each saved entity should have rnadom ID assigned to it """
        t1 = TestModel()
        t1.put()
        t2 = TestModel()
        t2.put()
        t3 = TestModel()
        t3.put()
        self.assertNotEqual(t1.random_id, t2.random_id)
        self.assertNotEqual(t2.random_id, t3.random_id)
        self.assertNotEqual(t1.random_id, t3.random_id)

    def test_random_id_regenerated(self):
        """ Random ID should be regenerated each time entity is saved """
        t = TestModel()
        t.put()
        r1 = t.random_id
        t.put()
        r2 = t.random_id
        self.assertNotEqual(r1, r2)

    def test_get_random(self):
        """ Should be able to fetch random entity """
        for i in range(200):
            TestModel().put()
        t1 = TestModel.random()
        t2 = TestModel.random()
        self.assertNotEqual(t1, t2)


class OwnershipMixinTestCase(DatastoreTestCase):

    def create_user(self, name='Foo', email='foo@test.com'):
        """ Helper method to create new user account """
        u = User(name=name, email=email)
        u.put()
        return u

    def test_assign_ownership(self):
        """ can assign ownership using the assign_owner() method """
        t = TestOwnerModel()
        u = self.create_user()
        t.assign_owner(u)
        t.put()
        self.assertEqual(t.owner, u.key)

    def test_is_owner(self):
        """ can check owner """
        t = TestOwnerModel()
        u1 = self.create_user()
        u2 = self.create_user('Bar', 'bar@test.com')
        t.assign_owner(u1).put()
        self.assertTrue(t.is_owner(u1))
        self.assertFalse(t.is_owner(u2))

    def test_get_owned_problems(self):
        """ can retrieve problems owned by some user """
        u = self.create_user()
        for i in range(10):
            TestOwnerModel(owner=u.key).put()
        owned = TestOwnerModel.get_by_owner(u)
        self.assertEqual(owned.count(), 10)


class ValidatorTestCase(DatastoreTestCase):

    def test_clean_method_retrns_dict(self):
        """ should return a dict """
        with mock.patch('formencode.validators.Email.to_python') as u:
            t = TestValidationModel(email='foo@test.com')
            d = t.clean()
            self.assertEqual(type(d), dict)
            self.assertTrue('email' in d, 'must have email key')

    def test_clean_calls_formencode_methods(self):
        """ calling clean() should call formencode methods """
        with mock.patch('formencode.validators.Email.to_python') as u:
            t = TestValidationModel(email='foo@test.com')
            d = t.clean()
            self.assertEqual(d['email'], u.return_value)

    def test_clean_throws_on_wrong_input(self):
        """ when entity has bad data, clean will throw """
        with self.assertRaises(TestValidationModel.ValidationError):
            t = TestValidationModel(email='not valid email')
            t.clean()

    def test_errors_format(self):
        """ when clean throws, we expect to see why it failed """
        t = TestValidationModel(email='not valid email')
        try:
            t.clean()
        except t.ValidationError, err:
            self.assertTrue(hasattr(err, 'errors'))
            self.assertTrue('email' in err.errors)
            self.assertTrue(isinstance(err.errors['email'],
                                       formencode.api.Invalid))


class AncestryTestCase(DatastoreTestCase):

    def test_is_unique(self):
        tp = TestAncestryParentModel()
        tp.put()
        self.assertTrue(TestAncestryModel.is_unique(tp.key.id(), 'bar'))
        tc = TestAncestryModel(id='bar', bar='bar', parent=tp.key)
        tc.put()
        self.assertFalse(TestAncestryModel.is_unique(tp.key.id(), 'bar'))


class UniquePropertyTestCase(DatastoreTestCase):

    def test_is_unique(self):
        """ is_unique tests for existing entity """
        TestUniqueModel(foo='bar', bar='foo').put()
        self.assertTrue(TestUniqueModel.is_unique(foo='baz', bar='foo'))
        self.assertFalse(TestUniqueModel.is_unique(foo='bar', bar='baz'))


if __name__ == '__main__':
    import unittest
    unittest.main()
