"""Pipes specific data from vSphere to SolarWinds"""
import atexit
import getpass
import requests
import sys
import urllib3

from interfaces.sw_interface import SolarWindsInterface
from interfaces.vsphere_interface import vSphereInterface
from pyVim import connect
from pyVmomi import vim
from vmware.vapi.vsphere.client import create_vsphere_client


# Get
def get_tags(client):
    """Collect list of tags"""
    department_tag_ids = []
    division_tag_ids = []

    # Get tags by category
    categories = client.tagging.Category.list()
    for category in categories:
        cat_info = client.tagging.Category.get(category)
        if cat_info.name == "DCI_OwnerDepartment":
            department_tag_ids = client.tagging.Tag.list_tags_for_category(
                category)
        elif cat_info.name == "DCI_OwnerDivision":
            division_tag_ids = client.tagging.Tag.list_tags_for_category(
                category)

    department = []
    division = []

    print("Retrieving DCI_OwnerDepartment tags and nodes")
    # Get vms by tags and pre-package for processing
    for tag in department_tag_ids:
        tag_nodes = [node.id for node in client.tagging.TagAssociation.list_attached_objects(tag)]
        name = client.tagging.Tag.get(tag).description
        category_id = client.tagging.Tag.get(tag).category_id
        tag_info = (name, category_id)
        department.append({(tag_info): tag_nodes})
    print("Retrieving DCI_OwnerDivision tags and nodes")
    for tag in division_tag_ids:
        tag_nodes = [node.id for node in client.tagging.TagAssociation.list_attached_objects(tag)]
        name = client.tagging.Tag.get(tag).description
        category_id = client.tagging.Tag.get(tag).category_id
        tag_info = (name, category_id)
        division.append({(tag_info): tag_nodes})

    return department, division


# Get
def get_vms(vcenter):
    # Get VM info and create dictionary of VM reference IDs and names
    vm = None
    entity_stack = vcenter.content.rootFolder.childEntity
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


# Process
def compare_vm_to_tags(client, tags, vms):
    print("Comparing VMs to Tags")
    for items in tags:
        for k, v in items.items():
            for vm in v:
                try:
                    vms[vm].append(k[0])
                except KeyError:
                    pass

# Push
def push_to_sw(sw, vms, nodes):
    for k, v in vms.items():
        try:
            updated_props = {'VCTR_OwnerDepartment': v[1]}
            sw.change_custom_properties(nodes[v[0].lower()], updated_props)
            updated_props = {'VCTR_OwnerDivision': v[2]}
            sw.change_custom_properties(nodes[v[0].lower()], updated_props)
            print(f"{v[0]} sent")
        except (KeyError, ValueError, IndexError) as e:
            pass


def main():
    print("By Adam P. Ashcraft - DTI/SA team")
    vsphere_username = input("vSphere Username: ")
    vsphere_password = getpass.getpass("vSphere Password: ")
    sw_username = input("Solarwinds Username: ")
    sw_password = getpass.getpass("Solarwinds Password: ")

    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Authenticate and create clients
    client = create_vsphere_client(
        server="",
        username=vsphere_username,
        password=vsphere_password,
        session=session
        )
    sw = SolarWindsInterface(sw_username, sw_password)

    vcenter = vSphereInterface(vsphere_password, vsphere_password)
    atexit.register(connect.Disconnect, vcenter)

    # Get (vSphere and SolarWinds)
    department = vcenter.get_tag("DCI_OwnerDepartment", client)
    division = vcenter.get_tag("DCI_OwnerDepartment", client)
    vms = vcenter.get_vms()

    query_str = """SELECT n.SysName, n.NodeID, n.Uri, n.Agent.AgentID
                   FROM Orion.Nodes n
                   WHERE n.Agent.AgentID is not null"""

    sw.query(query_str)
    nodes = sw.collect_uris()

    # Process
    compare_vm_to_tags(client, department, vms)
    compare_vm_to_tags(client, division, vms)

    # Push (Solarwinds)
    push_to_sw(sw, vms, nodes)

    # Write

    sys.exit()


if __name__ == '__main__':
    main()
