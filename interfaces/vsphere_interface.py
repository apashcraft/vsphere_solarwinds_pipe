import ssl

from pyVim import connect
from pyVmomi import vim


class vSphereInterface:

    def __init__(self, username, password, server):
        self.vsphere = self.auth(username, password, server)
        self.content = self.vsphere.RetrieveContent()

    def auth(self, username, password, server):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE

        vsphere = connect.SmartConnect(
            host=server,
            user=username,
            pwd=password)

        return vsphere

    def organize_vms(self, name):
        switch = {"prt3": "Tier3",
                  "tst3": "Tier3",
                  "dvt3": "Tier3",
                  "prt2": "Tier2",
                  "tst2": "Tier2",
                  "dvt2": "Tier2",
                  "prt1": "Tier1",
                  "tst1": "Tier1",
                  "dvt1": "Tier1",
                  "DOTDB": "DOT_Database",
                  "DOTAS": "DOT_App",
                  "DOTWS": "DOT_Web"}
        return switch.get(name, "Other_Servers")

    def get_nic_info(self, vm):
        nic = {}
        info = [vm.name]
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nic = {
                    device.deviceInfo.label:
                    f"Connected = {device.connectable.connected}"
                }
                info.append(nic)
        return info

    def print_session_id(self):
        session_id = self.vsphere.content.sessionManager.currentSession.key
        print(f"Session ID: {session_id}")

    def print_vsphere_info(self):
        info = self.vsphere.content.about
        print(f"Product Name: {info.fullName}")
        print(f"Product Build: {info.build}")
        print(f"Product Unique ID: {info.instanceUuid}")
        print(f"Product Version: {info.version}")
        print(f"Product Base OS: {info.osType}")
        print(f"Product Vendor: {info.vendor}")

    def get_vm_by_ip(self, ip):
        search_index = self.vsphere.content.searchIndex
        vm = search_index.FindByIp(None, ip, True)

        if not vm:
            print(f"{ip} not found")
        else:
            return vm

    def get_tags(self, category_name, client):
        """Collect list of tags and associated VMS"""
        tag_ids = []

        # Get categories
        categories = client.tagging.Category.list()
        for category in categories:
            cat_info = client.tagging.Category.get(category)
            if cat_info.name == category_name:
                tag_ids = client.tagging.Tag.list_tags_for_category(category)

        vms_per_tag = []

        # Get vms by tags and pre-package for processing
        print(f"Retrieving {category_name} tags and nodes")
        for tag in tag_ids:
            tag_nodes = [node.id for node in client.tagging.TagAssociation.list_attached_objects(tag)]
            name = client.tagging.Tag.get(tag).description
            category_id = client.tagging.Tag.get(tag).category_id
            tag_info = (name, category_id)
            vms_per_tag.append({(tag_info): tag_nodes})

        return vms_per_tag

    def get_vms(self):
        # Get VM info and create dictionary of VM reference IDs and names
        vm = None
        entity_stack = self.vsphere.content.rootFolder.childEntity
        vms = []
        print("Retrieving machine reference IDs")
        while entity_stack:
            vm = entity_stack.pop()
            try:
                vm_id = {str(vm.summary.vm)[20:-1]: [vm.name]}
                vms.append(vm_id)
            except AttributeError:
                pass
            if hasattr(vm, "childEntity"):
                entity_stack.extend(vm.childEntity)
            elif isinstance(vm, vim.Datacenter):
                entity_stack.append(vm.vmFolder)
        merged = {}
        for node in vms:
            merged.update(node)
        return merged
