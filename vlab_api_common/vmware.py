# -*- coding: UTF-8 -*-
"""
Common deploy functions
"""
import ssl
import time
import collections
from threading import Thread

from pyVim import connect
from pyVmomi import vim


class vCenter(object):
    """
    Interacts with the vSphere API via pyVmomi.
    The focus of this class is to make working with the vSphere API simpler, this
    comes a the cost of performance optimizations for correctness.

    :param host: **Required** The IP/FDQN to the vCenter server
    :type host: String

    :param user: **Required** The user account to authenticate with on the vCenter server
    :type user: String

    :param password: **Required** The user accounts password
    :type password: String

    :param port: The port to use when connecting to the vCenter server. Default is 443
    :type port: Integer

    :param verify: Set to False if you're using a self-signed TLS cert for vCenter
    :type verify: Boolean
    """

    def __init__(self, host, user, password, port=443, verify=True):
        if verify is False:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            context.verify_mode = ssl.CERT_NONE
        else:
            context = ssl._create_default_https_context
        self.conn = connect.SmartConnect(host=host, user=user, pwd=password,
                                         port=port, sslContext=context)

    def close(self):
        """
        Terminate the session to the vCenter server
        """
        connect.Disconnect(self.conn)

    def create_folder(self, new_folder, parent_dir='DS-IIQs'):
        """
        Creates a folder to store VMs within - helps keep our directory sane.

        Looking before leaping here due to a request from eng-inf

        :param new_folder: **Required** The name for the new folder
        :type new_folder: String

        :param parent_dir: The parent directory to create the new folder under.
                           Default is DS-IIQs
        :type parent_dir: String
        """
        parent_directory = self.get_by_name(vimtype=vim.Folder, name=parent_dir)
        for entity in parent_directory.childEntity:
            if entity.name == new_folder:
                break
        else:
            parent_directory.CreateFolder(new_folder)

    def get_by_name(self, vimtype, name, parent=None):
        """
        Find an object in vCenter by object name

        :param vimtype: The category of object to find
        :type vimtype: pyVmomi.VmomiSupport.LazyType

        :param name: The name of the object
        :type name: String

        :param parent: (Optional) Filter under a parent folder
        :type parent: String
        """
        if parent is None:
            bucket = self.get_by_type(vimtype)
        else:
            bucket = self.get_by_name(vim.Folder, parent).childEntity
        for item in bucket:
            if item.name == name:
                return item
        else:
            raise ValueError('Unable to locate object, Type: {0}, Name: {1}'.format(vimtype, name))

    def get_by_type(self, vimtype):
        """
        Returns a iterable view of vCenter objects

        :Returns: pyVmomi.VmomiSupport.ManagedObject

        :param vimtype: The category of object to find
        :type vimtype: pyVmomi.VmomiSupport.LazyType
        """
        if not isinstance(vimtype, collections.Iterable):
            vimtype = [vimtype]
        entity = self.content.viewManager.CreateContainerView(container=self.content.rootFolder,
                                                              type=vimtype,
                                                              recursive=True)
        return entity.view

    @property
    def content(self):
        """
        The fleeting state of vCenter objects

        :Returns: pyVmomi.VmomiSupport.vim.ServiceInstanceContent
        """
        return self.conn.RetrieveContent()

    @property
    def data_centers(self):
        """
        Return an iterable of available data centers

        :Returns: pyVmomi.VmomiSupport.ManagedObject
        """
        return self.get_by_type(vim.Datacenter)

    @property
    def resource_pools(self):
        """
        Return an iterable of available resource pools

        :Returns: pyVmomi.VmomiSupport.ManagedObject
        """
        return self.get_by_type(vim.ResourcePool)

    @property
    def networks(self):
        """
        Return an iterable of available networks

        :Returns: pyVmomi.VmomiSupport.ManagedObject
        """
        return self.get_by_type(vim.Network)

    @property
    def ovf_manager(self):
        """
        An object for working with OVFs in vCenter

        :Returns: pyVmomi.VmomiSupport.vim.OvfManager
        """
        return self.conn.content.ovfManager

    def get_ovf_lease(self, ovfd, datastore, user_folder, network, vm_name, timeout=30):
        """
        Required when attempting to deploy a new VM from an OVF

        :Returns: pyVmomi.VmomiSupport.vim.HttpNfcLease

        :Raises: RuntimeError if lease doesn't become usable before timeout

        :param ovfd: **Required** XML that defines the OVA - normally obtained by reading
                     in the .ovf file after untaring an OVA
        :type ovfd: String

        :param datastore: **Required** The name of a datastore to use when deploying the new VM
        :type datastore: String

        :param user_folder: **Required** The folder to put the new VM in
        :type user_folder: String

        :param network: **Required** The network to connect the new VM to
        :type network: String

        :param vm_name: **Required** The name to give the new VM
        :type vm_name: String

        :param timeout: How many seconds to wait for the lease to go from 'initializing'
                        to 'ready'. Default is 30 seconds
        :type timeout: Integer
        """
        # Network config
        netwk = self.get_by_name(vim.Network, network)
        net_mapper = vim.OvfManager.NetworkMapping()
        net_mapper.name = 'Network 1' # Defined in OVF file - very specific to IIQ's OVF
        net_mapper.network = netwk

        # Resource/Host
        ds = self.get_by_name(vim.Datastore, datastore)
        compute_hosts = self.get_by_type(vim.ClusterComputeResource)
        r_pool = compute_hosts[-1].resourcePool
        # any compute node/host works - the VM will be auto-moved based on load upon powering on
        host = compute_hosts[-1].host[0]

        # User folder
        folder = self.get_by_name(vim.Folder, user_folder)

        spec_params = vim.OvfManager.CreateImportSpecParams(entityName=vm_name,
                                                            networkMapping=[net_mapper])
        import_spec = self.ovf_manager.CreateImportSpec(ovfDescriptor=ovfd,
                                                        resourcePool=r_pool,
                                                        datastore=ds,
                                                        cisp=spec_params)

        lease = r_pool.ImportVApp(import_spec.importSpec, folder=folder, host=host)
        for _ in range(timeout):
            if lease.state == vim.HttpNfcLease.State.ready:
                return lease
            else:
                time.sleep(1)
        else:
            error = 'Lease for OVA deploy never became useable. Error: {0}'.format(lease.error)
            raise RuntimeError(error)

    def clone_template(self, template, datastore, user_folder, vm_name, parent=None, timeout=1200):
        """
        Deploy a new VM from a template

        :Returns: String, IP address of new VM

        :Raises: RuntimeError - when deploy times out, or new VM cannot get IP addr

        :param template: **Required** The name of the template
        :type template: String

        :param datastore: **Required** The name of a datastore to use when deploying the new VM
        :type datastore: String

        :param user_folder: **Required** The folder to put the new VM in
        :type user_folder: String

        :param vm_name: **Required** The name to give the new VM. **Must be unique**
        :type vm_name: String

        :param parent: (Optional) Specify a parent directory to locate the user_folder
        :type parent: String

        :param timeout: How many seconds to wait for the clone to complete, and for
                        the new VM to obtain a DHCP address. Default is 1200 (20 minutes)
        :type timeout: Integer
        """
        vm_template = self.get_by_name(vim.VirtualMachine, template)
        relospec = vim.vm.RelocateSpec()
        clonespec = vim.vm.CloneSpec()

        # config spec for where the new VM should go
        compute_hosts = self.get_by_type(vim.ClusterComputeResource)
        resource_pool = compute_hosts[0].resourcePool

        relospec.pool = resource_pool
        relospec.datastore = self.get_by_name(vim.Datastore, datastore)

        # config spec for clone operation
        clonespec.location = relospec
        clonespec.powerOn = True

        task = vm_template.Clone(folder=self.get_by_name(vim.Folder, user_folder, parent),
                                 name=vm_name,
                                 spec=clonespec)

        # clone template -> new vm
        for i in range(int(timeout / 2)):
            if task.info.state == 'success':
                break
            elif task.info.state == 'error':
                msg = task.info.error
                raise RuntimeError(msg)
            else:
                time.sleep(1)
        else:
            msg = 'Unable to deploy template {0} within {1} seconds'.format(template, int(timeout /2))
            raise RuntimeError(msg)

        # wait for DHCP address
        new_vm = self.get_by_name(vim.VirtualMachine, vm_name)
        for _ in range(int(timeout / 2)):
            if new_vm.summary.guest.ipAddress:
                return new_vm.summary.guest.ipAddress
            else:
                time.sleep(1)
        else:
            msg = 'Unable to obtain IP addr from template deploy. VM name is {0}'.format(vm_name)
            raise RuntimeError(msg)

    def vm_run_cmd(self, cmd_path, the_vm, cmd_args='', user='root', password='a'):
        """
        Execute a command on a given virtual machine.

        :Returns: vim.vm.guest.ProcessManager.ProcessInfo

        :param cmd_path: **Required** The absolute file path to the executable on the supplied virtual machine
        :type cmd_path: String

        :param cmd_args: he command arguments to pass to the executable
        :type cmd_args: String

        :param the_vm: **Required** The virtual machine to get process info about
        :type the_vm: vim.VirtualMachine

        :param user: The user account to use on the virtual machine. Default is 'root'
        :type user: String

        :param password: The password of the supplied user. Default is 'a'
        :type password: String
        """
        process_mgr = self.content.guestOperationsManager.processManager
        creds = vim.vm.guest.NamePasswordAuthentication(username=user,
                                                        password=password)

        program_spec = vim.vm.guest.ProcessManager.ProgramSpec(programPath=cmd_path,
                                                               arguments=cmd_args)
        pid = process_mgr.StartProgramInGuest(the_vm, creds, program_spec)
        time.sleep(1) # race between running command, and pyVmomi having info about it
        info = self.vm_process_table(the_vm, pids=[pid], user=user, password=password)

        return info[0]

    def vm_process_table(self, the_vm, pids=None, user='root', password='a'):
        """
        Obtain information about running processes on a given virtual machine

        :Returns: vim.vm.guest.ProcessManager.ProcessInfo

        :param the_vm: **Required** The virtual machine to get process info about
        :type the_vm: vim.VirtualMachine

        :param pids: A list of process ids to return info for. If not specified,
                     return info about all processes. Default is None
        :type pids: List of Long Integers. Example [1234L, 654L]

        :param user: The user account to use on the virtual machine. Default is 'root'
        :type user: String

        :param password: The password of the supplied user. Default is 'a'
        :type password: String
        """
        creds = vim.vm.guest.NamePasswordAuthentication(username=user,
                                                        password=password)
        if pids is None:
            pids = []
        info = self.content.guestOperationsManager.processManager.\
                            ListProcessesInGuest(vm=the_vm, auth=creds, pids=pids)
        return info

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class KeepAlive(Thread):
    """
    A thread to keep pinging vCenter so our lease doesn't expire while we deploy
    a new VM.
    """
    def __init__(self, lease, *args, **kwargs):
        self.lease = lease
        self.keep_running = True
        super(KeepAlive, self).__init__(*args, **kwargs)

    def run(self):
        while self.keep_running:
            time.sleep(5)
            try:
                self.lease.HttpNfcLeaseProgress(50) # any int works, 50 is just a random choice
                if self.lease.state == vim.HttpNfcLease.State.done:
                    self.keep_running = False
                    break
            except:
                self.keep_running = False
                break

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.keep_running = False
        self.lease.HttpNfcLeaseComplete()
        self.join()
