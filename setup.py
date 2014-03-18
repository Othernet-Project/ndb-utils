import os
from distutils.core import setup

setup(
    name='ndb-utils',
    description='Utilities for working with GAE NDB models',
    long_description=open(os.path.join(os.path.dirname(__file__),
                                       'README.rst')).read(),
    version='0.1a1',
    packages=['ndb_utils'],
    requires=[
        'FormEncode (>=1.3.0a1)',
    ],
    author='Outernet Project',
    author_email='branko@brankovukelic.com',
    url='https://github.com/Outernet-Project/ndb-utils',
    license='MIT',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
    ],
)
