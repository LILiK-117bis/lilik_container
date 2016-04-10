#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: lilik_container
short_description: Manage LXC Containers - Lilik style
version_added: 2.1.0
description:
  - Management of LXC containers
options:
    name:
        description:
	  - Name of a container
        required: true
    backing_store:
        choices:
          - dir
          - lvm
          - loop
          - btrfs
          - overlayfs
          - zfs
        description
	  - Backend storage type for the container.
        required: false
        default: lvm
    template:
        description:
          - Name of the template to use within an LXC create.
        required: false
        default: debian
    template_options:
       description:
          - Template options when building the container.
       required: false
       default: --release jessie
    lv_name:
        description:
          - Name of the logical volume, defaults to the container name.
        default: "vm_{{$CONTAINER_NAME}}"
        required: false
    vg_name:
       description:
         - If Backend store is lvm, specify the name of the volume group.
       default: sysvg
       required: false
    fs_type:
       description:
         - Create fstype TYPE.
       default: ext4
       required: false
    fs_size:
       description:
         - File system Size.
       default: 5G
       required: false
    container_command:
       description:
        - Run a command within a container.
       required: false
       default: apt-get update; apt-get install python
    state:
       choices:
        - started
        - stopped
        - restarted
        - absent
        - frozen
      description:
        - Define the state of a container.
      required: false
      default: started
requirements:
  - 'liblxc1 >= 1.1.5 # OS package'
  - 'python >= 2.6 # OS package'
  - 'lxc-python2 >= 0.1 #PIP package from https://github.com/lxc/python2-lxc'                       
"""

    
from ansible.module_utils.basic import *

class LilikContainer(object):
    """
    A generic lxc container manipulation object based on python-lxc
    """
    def __init__(self, module):
	self.module = module
        self.state = module.params['state']
        self.name = module.params['name']
        self.template = module.params['template']
        self.backing_store = module.params['backing_store']
        # handle default name
        self.lvname = module.params.get('lv_name', 'vm_%s' % module.params['name'])
        self.vgname = module.params['vg_name']
        self.fstype = module.params['fs_type']
        self.fssize = module.params['fs_size']

    def create_container(self):
        """
            Create a lxc.Container object as specified in the playbook, use it
            to create a lxc container and returns the reference 
        """
        container_options = {
           'bdev': self.backing_store,
           'lvname': self.lvname,
           'vgname': self.vgname,
           'fstype': self.fstype,
           'fssize': self.fssize,
           'bdev' : self.backing_store,
        }
        try:
            import lxc
        except ImportError:
            self.module.fail_json(changed=False, msg='Error importing lxc')

        container = lxc.Container(name = self.name)

        # TODO: python2-lxc does not like bdevtype but python-lxc does
        return container.create(
                    template = self.template,
                    args = container_options,
#                    bdevtype = self.backing_store
               )

def main():

    module = AnsibleModule(
        argument_spec = dict(
            backing_store = dict(
                                default='lvm',
                                choices=['dir', 'lvm', 'loop', 'btrsf', 'overlayfs', 'zfs',],
                                type='str',
            ),
            container_command = dict(
                                    type='str',
                                    default='apt-get update; apt-get install python',
            ),
            fs_size = dict(
                        required=False,
                        default='5G',
                        type='str',
            ),
            fs_type = dict(
                        required=False,
                        default='ext4',
                        type='str',
            ),
            lv_name = dict(
                        type='str',
            ),
            name = dict(
                    required=True,
                    type='str',
            ),
            state = dict(
                        default='started',
                        choices=['started', 'stopped', 'restarted', 'absent', 'frozen'],
                        type='str',
            ),
            template = dict(
                        required=False,
                        default='debian',
                        type='str',
            ),
            template_options = dict(required=False),
            vg_name = dict(
                        required=False,
                        default='sysvf',
                        type='str',
            ),
        )
    )

    try:
        import lxc
    except ImportError:
        module.fail_json(changed=False, msg='liblxc is required for this module to work')

    lilik_container = LilikContainer(module)

    result = {}
    result['name'] = lilik_container.name
    result['state'] = lilik_container.state

    if lilik_container.state == 'absent':
        
        # destroy the container
        if lilik_container.destoy():
            module.exit_json(changed=True)
        
        # TODO: remove redundant test
        # test wether the container is absent or not
        if lilik_container.name in lxc.list_containers():
            module.fail_json(changed=False)

        # the container has been removed
        else:
            module.exit_json(changed=True)
        # end TODO: remove redundant test

    elif lilik_container.state in ['started', 'stopped', 'restarted', 'frozen']:

        # the container exists, just set the state as required       
        if lilik_container.name in lxc.list_containers():

            container_actions_from_state = {
                'started': lilik_container.start,
                'stopped': lilik_container.stop,
                'restarted': lilik_container.restart,
                'frozen': lilik_container.freeze,
            }
            
            # selected action
            action = container_actions.get(container.state)

            if action():
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

        # the container does not exists, create it
        else:
            try:
                new_container = lilik_container.create_container()
                module.exit_json(changed=True)
            except Exception as e:
                module.fail_json(
                        changed=False,
                        msg='An excption was raised while creating the container',
                        exception_message=str(e),
                )

if __name__ == '__main__':
    main()
