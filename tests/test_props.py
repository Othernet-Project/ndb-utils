import unittest
from decimal import *

from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError

import formencode
from formencode import validators

from ndb_utils.properties import *

from dbunit import DatastoreTestCase


class TestEmail(ndb.Model):
    email = EmailProperty()
    email_required = EmailProperty(required=True)


class TestSlug(ndb.Model):
    slug = SlugProperty()
    slug_required = SlugProperty(required=True)


class TestDecPropModel(ndb.Model):
    dec = DecimalProperty()
    precise = DecimalProperty(float_prec=10)


class EmailPropertyTestCase(DatastoreTestCase):

    def test_email_strips_emails(self):
        """ emails should be stripped """
        t = TestEmail(email=' foo@test.com ', email_required=' foo@test.com ')
        self.assertEqual(t.email, 'foo@test.com')
        self.assertEqual(t.email_required, 'foo@test.com')

    def test_email_validation_does_not_double_required(self):
        """ email validator should not double as ``required`` parameter """
        try:
            t = TestEmail(email_required='foo@test.com')
        except Exception:
            self.assertTrue(False, 'leaving off non-required email should not '
                            'raise')

    def test_malformed_email(self):
        """ malformed emails should raise ``BadValueError`` """
        with self.assertRaises(BadValueError):
            t = TestEmail(email='foo', email_required='foo@test.com')

    def test_should_be_lowercased(self):
        """ output email should be stripped and lower-cased """
        t = TestEmail(email=' Foo@Test.COM ', email_required=' Foo@Test.COM ')
        self.assertEqual(t.email, 'foo@test.com')
        self.assertEqual(t.email_required, 'foo@test.com')


class SlugPropertyTestCase(DatastoreTestCase):

    def test_should_not_require(self):
        try:
            t = TestSlug(slug_required='foo')
        except Exception:
            self.assertTrue(False, 'should not throw for non-required slug')

    def test_failure_on_bad_slug(self):
        """ should throw ``BadValueError`` on bad slug"""
        with self.assertRaises(BadValueError):
            t = TestSlug(slug='fooo bar baz', slug_required='foo')


class DecimalStringValidatorTestCase(unittest.TestCase):

    def test_conversion_to_decimal(self):
        """ basic functionality should be good """
        v = DecimalString()
        self.assertEqual(v.to_python('12'), Decimal('12'))

    def test_raises_on_non_numeric_values(self):
        """ should raise on non-numeric values as expected """
        v = DecimalString()
        with self.assertRaises(formencode.Invalid):
            v.to_python('foo')

    def test_raises_on_minimum_and_maximum(self):
        """ should raise on out of bound values as expected """
        v = DecimalString()
        with self.assertRaises(formencode.Invalid):
            v.to_python('-1')
        with self.assertRaises(formencode.Invalid):
            v.to_python('100000000000')

    def test_customizing_min_and_max(self):
        """ should be able to set min and max """
        v = DecimalString(min=-1, max=100000000000)

        try:
            v.to_python('-1')
        except formencode.Invalid:
            self.assertTrue(False, 'should not raise for minimum')

        try:
            v.to_python('100000000000')
        except formencode.Invalid:
            self.assertTrue(False, 'should not raise for maximum')

    def test_accepts_numbers(self):
        """ should also work with numbers, not just strings """
        v = DecimalString()
        self.assertEqual(v.to_python(20), Decimal('20'))


class DecimalPropertyTestCase(DatastoreTestCase):

    def test_conversion_of_data(self):
        """ the value should be serialized into integer before put() """
        d = DecimalProperty()
        s = d._to_base_type(Decimal('12'))
        self.assertEqual(s, 1200)

    def test_conversion_to_decimal(self):
        """ value should be converted back to decimal from string """
        d = DecimalProperty()
        v = d._from_base_type(12)
        self.assertEqual(v, Decimal('0.12'))

    def test_storing_and_retrieval(self):
        """ test storing and retrieving entity using DecimalProperty """
        TestDecPropModel(dec='2.433').put()
        t = TestDecPropModel.query().get()
        self.assertEqual(t.dec, Decimal('2.43'))

    def test_storing_and_retrieval(self):
        """ test storing and retrieving entity using DecimalProperty """
        TestDecPropModel(dec='2.438').put()
        t = TestDecPropModel.query().get()
        self.assertEqual(t.dec, Decimal('2.44'))

    def test_setting_arbitrary_precision(self):
        """ can use higher floating point precision """
        t = TestDecPropModel(precise='2.4123')
        t.put()
        t1 = t.key.get()
        self.assertEqual(t1.precise, Decimal('2.4123'))

    def test_lookup_equal(self):
        t = TestDecPropModel(dec='12.2')
        t.put()
        t1 = TestDecPropModel.query(TestDecPropModel.dec=='12.2').get()
        self.assertEqual(t, t1)

    def test_lookups(self):
        t = TestDecPropModel(dec='12.2')
        t.put()
        t1 = TestDecPropModel.query(TestDecPropModel.dec=='12.2').get()
        t2 = TestDecPropModel.query(TestDecPropModel.dec>='12').get()
        t3 = TestDecPropModel.query(TestDecPropModel.dec<='13').get()
        t4 = TestDecPropModel.query(TestDecPropModel.dec!='12.2').fetch()
        self.assertEqual(t, t1)
        self.assertEqual(t, t2)
        self.assertEqual(t, t3)
        for entity in t4:
            self.assertNotEqual(entity, t)

    def test_lookups_using_integer_arguments(self):
        t = TestDecPropModel(dec='15')
        t.put()
        t1 = TestDecPropModel.query(TestDecPropModel.dec==15).get()
        t2 = TestDecPropModel.query(TestDecPropModel.dec>=14).get()
        t3 = TestDecPropModel.query(TestDecPropModel.dec<=16).get()
        t4 = TestDecPropModel.query(TestDecPropModel.dec!=15).fetch()
        self.assertEqual(t, t1)
        self.assertEqual(t, t2)
        self.assertEqual(t, t3)
        for entity in t4:
            self.assertNotEqual(entity, t)


if __name__ == '__main__':
    unittest.main()

