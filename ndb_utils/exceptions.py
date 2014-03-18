from __future__ import unicode_literals, print_function

__all__ = ['ModelError', 'BadKeyValueError', 'DuplicateEntityError',
           'ValidationError']


class ModelError(Exception):
    """ Generic exception for utils module """
    pass


class BadKeyValueError(ModelError):
    """ Raised when value used for a key is missing """
    pass


class DuplicateEntityError(ModelError):
    """ Helper exception that can be thrown by models implementing KeyMixin """
    pass


class ValidationError(Exception):
    """ Raised when validation fails in the ValidatingMixin """
    def __init__(self, message, errors, *args, **kwargs):
        self.errors = errors
        super(ValidationError, self).__init__(message, *args, **kwargs)


