from __future__ import unicode_literals, print_function

import re
from decimal import Decimal

import formencode

from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError


__all__ = ['DecimalString', 'slug_validator', 'email_validator',
           'SlugProperty', 'EmailProperty', 'DecimalProperty']


class DecimalString(formencode.validators.FancyValidator):
    """ Custom validator for handling decimal values """
    min = 0
    max = 999999999
    precision = 12
    numeric_re = re.compile(r'^-?\d+(\.\d+)?$')

    messages = {
        'too_small': 'Number cannot be smaller than %s' % min,
        'too_large': 'Number cannot be larger than %s' % max,
        'not_a_number': '%(nan)s is not a numeric value',
    }

    def __init__(self, min=None, max=None, precision=None, *args, **kwargs):
        if min is not None:
            self.min = min
        if max is not None:
            self.max = max
        if precision is not None:
            self.precision = precision
        super(DecimalString, self).__init__(*args, **kwargs)

    def _convert_to_python(self, value, state):
        return Decimal(value)

    def _validate_other(self, value, state):
        value = unicode(value)
        if not self.numeric_re.match(value):
            raise formencode.Invalid(self.message('not_a_number', state,
                                                  nan=value), value, state)

    def _validate_python(self, value, state):
        if value < self.min:
            raise formencode.Invalid(self.message('too_small', state),
                                     value, state)
        if value > self.max:
            raise formencode.Invalid(self.message('too_large', state),
                                     value, state)


slug_validator = formencode.validators.Regex(r'^[\w-]+$')
email_validator = formencode.validators.Email(strip=True)
decimal_validator = DecimalString()


class SlugProperty(ndb.StringProperty):
    """ Property that stores slugs """

    def _validate(self, value):
        if not value:
            return None
        try:
            return slug_validator.to_python(value)
        except formencode.api.Invalid, err:
            raise BadValueError(err)


class EmailProperty(ndb.StringProperty):
    """ Property that stores and validates Email addresses """

    def _validate(self, value):
        if not value:
            return None
        try:
            value = unicode(value).lower()
        except TypeError:
            raise BadValueError(formencode.Invalid('Invalid value', value))

        try:
            return email_validator.to_python(value)
        except formencode.api.Invalid, err:
            raise BadValueError(err)


class DecimalProperty(ndb.IntegerProperty):
    """ Property that stores Python Decimal objects """

    float_prec = 2

    def __init__(self, float_prec=None, **kwargs):
        if float_prec is not None:
            self.float_prec = float_prec
        super(DecimalProperty, self).__init__(**kwargs)

    def _validate(self, value):
        return decimal_validator.to_python(value)

    def _to_base_type(self, value):
        return int(round(value * (10 ** self.float_prec)))

    def _from_base_type(self, value):
        return Decimal(value) / (10 ** self.float_prec)

