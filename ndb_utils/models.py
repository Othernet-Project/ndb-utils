"""
Various helpers for managing models
"""

from __future__ import unicode_literals, print_function

import random

from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
import formencode

from .exceptions import *

MAX_RAND = 999999999999
RAND_SAMPLE_SIZE = 10


__all__ = ['ValidationError', 'TimestampedMixin', 'RandomMixin',
           'UniqueByAncestryMixin', 'UniquePropertyMixin', 'OwnershipMixin',
           'ValidatingMixin']


class TimestampedMixin(object):
    """ Mixin that adds creation and update timestamps """
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)


class RandomMixin(object):
    """ Mixin that allows fetching of random entity """

    random_id = ndb.IntegerProperty(required=True)

    @classmethod
    def random(cls):
        r = cls.generate_random()
        sample = cls.query(cls.random_id > r).fetch(RAND_SAMPLE_SIZE)
        return random.choice(sample)

    @classmethod
    def generate_random(cls):
        return random.randint(0, MAX_RAND)

    def _pre_put_hook(self):
        self.random_id = self.generate_random()
        super(RandomMixin, self)._pre_put_hook()


class UniqueByAncestryMixin(object):
    """ Mixin that provides helpful methods for establishing uniqueness """

    ancestry_path = []

    DuplicateEntityError = DuplicateEntityError

    @classmethod
    def get_ancestry_pairs(cls, *args):
        ancestry = cls.ancestry_path
        ancestry.append(cls._get_kind())
        return zip(ancestry, args)

    @classmethod
    def is_unique(cls, *args):
        key = ndb.Key(pairs=cls.get_ancestry_pairs(*args))
        return key.get() is None

    @classmethod
    def duplicate_error(cls, *args):
        ancestry = cls.ancestry_path
        ancestry.append(cls._get_kind())
        raise cls.DuplicateEntityError(
            'Entity with key %s exists' % (', '.join(
                cls.get_ancestry_pairs(*args))))


class UniquePropertyMixin(object):
    """ Mixin that provides methods that test for uniqueness """

    unique_properties = []

    DuplicateEntityError = DuplicateEntityError

    @classmethod
    def is_unique(cls, **kwargs):
        query_args = []
        for prop in cls.unique_properties:
            query_args.append(getattr(cls, prop) == kwargs.get(prop))
        return cls.query(ndb.OR(*query_args)).count() == 0

    @classmethod
    def duplicate_error(cls):
        raise cls.DuplicateEntityError(
            'Entity with specified %s exists' % (', '.join(
                cls.unique_properties)))


class OwnershipMixin(object):
    """ Mixin that allows permission checks """

    owner = ndb.KeyProperty(kind='User', required=True)

    def assign_owner(self, owner):
        """ Assigns owner to the entity """
        self.owner = self._get_key(owner)
        return self

    def is_owner(self, owner):
        """ Returns boolean test result of ownership """
        return self.owner == self._get_key(owner)

    @classmethod
    def get_by_owner(cls, owner):
        """ get all entities owned by specified owner """
        return cls.query(cls.owner==cls._get_key(owner))

    @classmethod
    def _get_key(cls, owner):
        """ Ensures owner is a key and not entity """
        if hasattr(owner, 'key'):
            return owner.key
        return owner


class ValidatingMixin(object):
    validate_schema = {}
    validate_on_put = True
    ValidationError = ValidationError

    def clean(self):
        """ Cleans the data and throws ValidationError on failure """
        errors = {}
        cleaned = {}

        for name, validator in self.validate_schema.items():
            val = getattr(self, name, None)
            try:
                cleaned[name] = validator.to_python(val)
            except formencode.api.Invalid, err:
                errors[name] = err

        if errors:
            raise ValidationError('Invalid data', errors)
        return cleaned

    def _pre_put(self):
        """ Pre-put hook to validate data and set the cleaned values """
        if not self.validate_on_put:
            return
        self.populate(**self.clean())


