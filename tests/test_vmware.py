# -*- coding: UTF-8 -*-
"""
A unit tests for the vCenter object
"""
from unittest.mock import MagicMock, patch
from collections import namedtuple
import unittest
from pyVmomi import vim

from vlab_api_common import vmware


class EmptyObject(object):
    """
    Derpy class for making objects with arbitrary attributes
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestvCenter(unittest.TestCase):
    """
    A suite of test cases for the vCenter object
    """

    @patch.object(vmware, 'connect')
    def setUp(self, mocked_connect):
        """Runs before each test case"""
        self.mocked_connect = mocked_connect
        self.vc = vmware.vCenter(host='vcenter.com', user='sam', password='ilovekats')

    @patch.object(vmware, 'connect')
    def test_close(self, mocked_connect):
        """vCenter.close - happy path works"""
        # Had to mock locally for the ref to the mock object to work correctly
        self.vc = vmware.vCenter(host='vcenter.com', user='sam', password='ilovekats')
        self.vc.close()

        self.assertEqual(True, mocked_connect.Disconnect.called)

    def test_create_folder(self):
        """vCenter.create_folder - happy path works"""
        self.vc.get_by_name = MagicMock()
        fake_parent_dir = MagicMock()
        self.vc.get_by_name.return_value = fake_parent_dir

        self.vc.create_folder('new_folder_woot', parent_dir='some_dir')

        self.assertEqual(True, fake_parent_dir.CreateFolder.called)

    def test_create_folder_duplicate(self):
        """vCenter.create_folder - we don't blow up if the folder already exists"""
        FakeFolder = namedtuple('FakeFolder', 'name')

        self.vc.get_by_name = MagicMock()
        self.vc.get_by_name.return_value.childEntity = [FakeFolder('new_folder_woot')]

        self.vc.create_folder('new_folder_woot', parent_dir='some_dir')

        self.assertEqual(False, self.vc.get_by_name.return_value.CreateFolder.called)

    def test_create_folder_value_error(self):
        """vCenter.create_folder - we raise ValueError if the parent dir doesn't exist"""
        self.assertRaises(ValueError, self.vc.create_folder, 'new_folder')

    def test_get_by_name_value_error(self):
        """vCenter.get_by_name - raises ValueError if no objects found"""
        self.assertRaises(ValueError, self.vc.get_by_name, vimtype='sometype', name='thing')

    def test_get_by_name(self):
        """vCenter.get_by_name - happy path works"""
        self.vc.get_by_type = MagicMock()
        expected = EmptyObject(name='some_dir')
        self.vc.get_by_type.return_value = [expected]

        output = self.vc.get_by_name(vimtype='sometype', name='some_dir')

        self.assertEqual(output, expected)

    def test_get_by_type(self):
        """vCenter.get_by_type - happy path works"""
        fake_entity = EmptyObject(view=[1,2,3])
        self.vc.content.viewManager.CreateContainerView.return_value = fake_entity

        output = self.vc.get_by_type(vimtype='sometype')
        expected = [1,2,3]

        self.assertEqual(output, expected)

    def test_get_by_type_iterable(self):
        """vCenter.get_by_type - if provided vimtype is not iterable, we make it an iterable"""
        fake_entity = EmptyObject(view=[1,2,3])
        self.vc.content.viewManager.CreateContainerView.return_value = fake_entity

        output = self.vc.get_by_type(vimtype=1)
        expected = [1,2,3]

        self.assertEqual(output, expected)

    def test_content(self):
        """vCenter.content - happy path works"""
        fake_conn = MagicMock()
        self.vc.conn = fake_conn

        self.vc.content

        self.assertEqual(True, fake_conn.RetrieveContent.called)

    def test_content_property_no_delattr(self):
        """vCenter.content - does not support delattr"""
        self.assertRaises(AttributeError, delattr, self.vc, 'content')


    def test_content_property_no_setattr(self):
        """vCenter.content - does not support setattr"""
        self.assertRaises(AttributeError, setattr, self.vc, 'content', 'woot')

    def test_data_centers(self):
        """vCenter.data_centers - happy path works"""
        fake_entity = EmptyObject(view=[1,2,3])
        self.vc.content.viewManager.CreateContainerView.return_value = fake_entity

        output = self.vc.data_centers
        expected = [1,2,3]

        self.assertEqual(output, expected)

    def test_data_centers_property_no_delattr(self):
        """vCenter.data_centers - does not support delattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, delattr, self.vc, 'data_centers')

    def test_data_centers_property_no_setattr(self):
        """vCenter.data_centers - does not support setattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, setattr, self.vc, 'data_centers', 'woot')

    def test_resource_pools(self):
        """vCenter.resource_pools - happy path works"""
        fake_entity = EmptyObject(view=[1,2,3])
        self.vc.content.viewManager.CreateContainerView.return_value = fake_entity

        output = self.vc.resource_pools
        expected = [1,2,3]

        self.assertEqual(output, expected)

    def test_resource_pools_property_no_delattr(self):
        """vCenter.resource_pools - does not support delattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, delattr, self.vc, 'resource_pools')

    def test_resource_pools_property_no_setattr(self):
        """vCenter.resource_pools - does not support setattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, setattr, self.vc, 'resource_pools', 'woot')

    def test_ovf_manager_property_no_delattr(self):
        """vCenter.ovf_manager - does not support delattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, delattr, self.vc, 'ovf_manager')

    def test_ovf_manager_property_no_setattr(self):
        """vCenter.ovf_manager - does not support setattr"""
        self.get_by_type = MagicMock()
        self.assertRaises(AttributeError, setattr, self.vc, 'ovf_manager', 'woot')

    @patch.object(vmware, 'connect')
    def test_context_management(self, mocked_connect):
        """vCenter - object can be used with 'with' statement"""
        faked_close = MagicMock()
        with vmware.vCenter(host='vcenter.com', user='sam', password='ilovekats') as derp:
            derp.close = faked_close

        self.assertEqual(True, faked_close.called)

    @patch.object(vmware.vim.OvfManager, 'CreateImportSpecParams')
    @patch.object(vmware.vim.OvfManager, 'NetworkMapping')
    @patch.object(vmware.time, 'sleep')
    def test_ovf_lease(self, mocked_sleep, mocked_networkmapping, mocked_create_params):
        """vCenter.get_ovf_lease - happy path works"""
        self.vc.get_by_type = MagicMock()
        self.vc.ovf_manager.CreateImportSpec = MagicMock()
        fake_lease = EmptyObject(state='ready')
        fake_pool = EmptyObject(ImportVApp=lambda x, folder=None, host=None: fake_lease)
        fake_obj = EmptyObject(name='some_object',
                               resourcePool = fake_pool,
                               host='somehost')
        self.vc.get_by_type.return_value = [fake_obj]

        output = self.vc.get_ovf_lease(ovfd='ovfd',
                                       datastore='some_object',
                                       user_folder='some_object',
                                       network='some_object',
                                       vm_name='some_object')
        expected = 'woot'

        self.assertEqual(output, fake_lease)

    @patch.object(vmware.vim.OvfManager, 'CreateImportSpecParams')
    @patch.object(vmware.vim.OvfManager, 'NetworkMapping')
    @patch.object(vmware.time, 'sleep')
    def test_ovf_lease_runtime_error(self, mocked_sleep, mocked_networkmapping, mocked_create_params):
        """vCenter.get_ovf_lease - if the lease is never ready, we raise RuntimeError"""
        self.vc.get_by_type = MagicMock()
        self.vc.ovf_manager.CreateImportSpec = MagicMock()
        fake_lease = EmptyObject(state='not ready', error='testing')
        fake_pool = EmptyObject(ImportVApp=lambda x, folder=None, host=None: fake_lease)
        fake_obj = EmptyObject(name='some_object',
                               resourcePool = fake_pool,
                               host='somehost')
        self.vc.get_by_type.return_value = [fake_obj]

        self.assertRaises(RuntimeError, self.vc.get_ovf_lease, ovfd='ovfd',
                                                               datastore='some_object',
                                                               user_folder='some_object',
                                                               network='some_object',
                                                               vm_name='some_object')


class TestKeepAlive(unittest.TestCase):
    """
    A suite of test cases for the KeepAlive object
    """

    @patch.object(vmware.time, 'sleep')
    def test_keepalive(self, mocked_sleep):
        """KeepAlive - happy path works"""
        fake_lease = MagicMock()
        fake_lease.state = vim.HttpNfcLease.State.done

        thread = vmware.KeepAlive(fake_lease)
        thread.run()

        self.assertEqual(False, thread.keep_running)

    @patch.object(vmware.time, 'sleep')
    def test_keepalive_exception(self, mocked_sleep):
        """KeepAlive - other happy path works"""
        fake_lease = MagicMock()
        fake_lease.HttpNfcLeaseProgress.side_effect = RuntimeError('testing')

        thread = vmware.KeepAlive(fake_lease)
        thread.run()

        self.assertEqual(False, thread.keep_running)

    @patch.object(vmware.time, 'sleep')
    def test_keepalive_context_management(self, mocked_sleep):
        """KeepAlive - works when used with a 'with' statement"""
        fake_lease = MagicMock()
        fake_lease.HttpNfcLeaseProgress.side_effect = RuntimeError('testing')
        with vmware.KeepAlive(fake_lease):
            pass

        self.assertEqual(True, fake_lease.HttpNfcLeaseProgress.called)


if __name__ == '__main__':
    unittest.main()
