import unittest
import time

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util


class DatastoreTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)  # simulates high-replication datastore
        self.testbed.init_datastore_v3_stub(self.policy)  # required by ndb
        self.testbed.init_memcache_stub()  # required by ndb
        self.testbed.init_blobstore_stub()
        self.testbed.init_files_stub()  # required by blobstore

    def tearDown(self):
        self.testbed.deactivate()

    def assertBlobDoesNotExist(self, key):
        """ Assert absence of a Blobstore blob """
        self.assertEqual(BlobInfo.get(key), None,
                         'Expected blob %s to not exist' % key)

