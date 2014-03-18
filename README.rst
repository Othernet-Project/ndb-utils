=========
NDB utils
=========

Set of utilities for working with Google AppEngine Datastore.

The pckage currently has a few mixins for GAE NDB models, and a few custom
properties.

NDB utils require FormEncode if you are using custom properties.

Installation
============

TODO

Model mixins
============

NDB utils comes with a few mixins for making common modelling tasks easier.

ndb_utils.models.TimestampedMixin
---------------------------------

This mixin adds two properties to your models: ``created`` (creation
timestamp), and ``updated`` (update timestamp). These are both 
``ndb.DateTimeProperty`` with ``auto_now_add`` and ``auto_now`` respectively.

ndb_utils.models.RandomMixin
----------------------------

Mixin provides means for retrieving a random entity. Since retrieving all
entites in order to pick a random item from the list would be too CPU
intensive, this model mixin adds a ``random_id`` property, which contains a
randomly generated integer which is used to look up 'random' entities. The
random number is assigned in a ``_pre_put_hook``.

During querying, it samples from the database a subset of 10 entities whose
``random_id`` is larger than another randomly generated integer and chooses a 
random entity from the sample.

This is obviously not a sure-fire way to retrieve a random entity. The random
number generated during lookup may be larger than any of the random numbers in
the database, so another query may be needed.

The mixin adds one classmethod used to retrieve a random entity:
``RandomMixin.random()``. Calling this classmethod will retreive one random
entity.

There is also a utility method ``RandomMixin.generate_random()`` which
generates a random integer.

ndb_utils.models.UniqueByAncestryMixin
--------------------------------------

This mixin provides a method for checking uniqueness for a specified ancestry
chain. This is best illustrated by example. ::

    >>> from google.appengine.ext import ndb
    >>> from ndb_utils.models import UniqueByAncestryMixin
    >>> class Foo(ndb.Model):
    ...     prop = ndb.StringProperty()
    >>> class Bar(ndb.Model):
    ...     prop = ndb.StringProperty()
    >>> class Baz(UniqueByAncestryMixin, ndb.Model):
    ...     ancestry_path = ['Foo', 'Bar']
    ...     prop = ndb.StringProperty()
    >>> foo = Foo(id='foo')
    >>> bar = Bar(id='bar', parent=foo.key)
    >>> baz = Baz(id='baz', parent=bar.key)
    >>> ndb.put_multi([foo, bar, baz])
    >>> Baz.is_unique('foo', 'bar', 'baz')
    False

To break down the above, we define a model which specifies the ancestry path.
The ``ancestry_path`` property is optional, and should be a list of ancestor
kinds. The model's own kind is implied, and will be appended to the ancestry
path automatically.

The ``UniqueByAncestryMixin.is_unique()`` classmethod takes any number of
positional arguments, which are interpolated into the ancestry path to build a
pair of kind-id pairs used to build a key. In the example above, we are passing
in (in order), the ``Foo``'s id, then ``Bar``'s id, and finally the ``Baz``'s
id, in order to test for uniqueness of the resulting key ``[('Foo', 'foo'),
('Bar', 'bar'), ('Baz', 'baz')]``.

The method returns a boolean that is ``True`` if the resulting key is not in
use.

Note that this mixin is only useful if the id's of all ancestors, as well as of
the entity itself are known in advance. If your model uses an integer id
provided by the datastore, you cannot use this mixin. (See the
``UniquePropertyMixin`` for an alternative solution.)

Usually, you want to check for uniqueness when creating a new entity. When
doing so, note that no ancestor query is performed, and thus the
``is_unique()`` method cannot be used within transactions.

If you prefer to raise an exception when there is a clash, there is an
exception class provided by NDB utils. You can raise this exception manually
using the ``UniquePropertyMixin.DuplicateError`` class, or
``ndb_utils.exceptions.DuplicateError``, or by calling the
``duplicate_error()`` classmethod passing it the same argument you passed to
``is_unique()``. The last method is only a cosmetic thing. It provides a
standard error message and nothing more.

ndb_utils.models.UniquePropertyMixin
------------------------------------

This mixin provides methods for checking uniqueness of a set of properties
across the datastore for a particular model. The properties that are to be
checked are declared using the ``unique_properties`` class property.

Let's take a look at an example::

    >>> from google.appengine.ext import ndb
    >>> from ndb_utils.models import UniquePropertyMixin
    >>> class Foo(UniquePropertyMixin, ndb.Model):
    ...     unique_properties = ['prop']
    ...     prop = ndb.StringProperty()
    >>> foo = Foo(prop='foo')
    >>> foo.put()
    >>> Foo.is_unique(prop='foo')
    False
    >>> Foo.is_unique(prop='bar')
    True

Unlike the ``UniqueByAncestryMixin``, the ``is_unique()`` method takes a set of
keyword arguments matching the property-value pairs. Only the arguments whose
names match the properties listed in the ``unique_properties`` list will be
used. The method performs a ``count()`` query internally to test for existence
of any entities matching the specified properties, and returns ``True`` if
there are none.

The current implementation allows a bit more flexibility than useful. There are
no checks to catch the situations where properties listed in
``unique_properties`` list are proper properties (you will get an
``AttributeError`` when you call ``is_unique`` with wrong properties listed),
and you are not required to test all listed properties either when calling
``is_unique()``. It's up to the developer to make sure uniqueness tests are
successful.

Also note that the query performed in ``is_unique()`` method is not an ancestor
query, so this method cannot be used inside transactions.

ndb_utils.models.OwnershipMixin
-------------------------------

``OwnershipMixin`` is used to assign owners to entities. The ownership is
established through a ``KeyProperty`` named ``owner``. The kind of the owner
entity should be called 'User', and owner is required.

The mixin provides two methods. One is the ``assign_owner()`` method, which
takes either an owner entity or its key and assigns the key to the ``owner``
property. The other method is ``is_owner()`` which takes an owner entity or its
key and tests if the entity is owned by the entity.

The mixin also provides a classmethod, ``get_by_owner()`` which takes either an
owner entity or its key and returns a query object filtered by owner.

ndb_utils.models.ValidatingMixin
--------------------------------

This mixin provides methods for validating model instances on ``put()`` or
manually. The API for this mixin is still being worked out, so consider it
strictly experimental.

Validation uses FormEncode_ under the hood, so you will need to be(come)
familiar with `its API`_.

The model should have a validation schema, which is a simple dictionary mapping
property names to validators. At the moment, we are not using the FormEncode's
``Schema`` class, but expect the dictionary schema to be replaced with
FormEncode schema in future.

Here is a simple example with an email field::

    >>> from google.appengine.ext import ndb
    >>> from formencode.validators import Email
    >>> from ndb_utils.models import ValidatingMixin
    >>> class Foo(ValidatingMixin, ndb.Model):
    >>>     validate_schema = {'prop': Email()}
    >>>     prop = ndb.StringProperty()
    >>> f1 = Foo(prop='invalid_email')
    >>> f1.put()
    Traceback (most recent call last):
    ...
    ValidationError: ...
    >>> f2 = Foo(prop='good@email.com')
    >>> f1.put()

The ``ValidationError`` exception can be accessed as a property on the model::

    >>> try:
    ...     f1.put()
    ... except Foo.ValidationError:
    ...     print 'Not a valid email'

Internally, when ``put()`` is called, the ``clean()`` instance method is called
in the ``_pre_put()`` hook. This method goes over all keys in the schema, and
calls the validator's ``to_python()`` method on the value of the property. If
the validator raises ``formencode.Invalid`` exception, it remembers the error
and continues. When all validation schema keys are processed, it raises the
``ValidationError`` exception if there had been any errors.

Repeated properties are currently not supported. This is planned for future
releases. Meanwhile, you can create a custom validator to validate repeated
properties.

If you prefer to always validate manually, you can set the ``validate_on_put``
class property to ``False`` and call the ``clean()`` method manually.

The ``clean()`` method returns cleaned data, instead of assigning them to
properties, so you will need to call ``populate()`` on the instance to assign
the new values. For instance::

    >>> try:
    ...     f1.populate(**f1.clean())
    ... except Foo.ValidationError:
    ...     print 'Not a valid email'

Property mixins
===============

The GAE utils


.. _FormEncode: http://www.formencode.org/en/latest/
.. _its API: http://www.formencode.org/en/latest/Validator.html
