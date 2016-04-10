

# rewrite of the create_container playbook in Python; this happens because
# the module for LXC container shipped with ansible is not working right now
#import lxc

# liliks infrastructure
#container_name = "gogs"
#logical_volume_name = "vm_gogs"
#lvm_volume_group = "sysvg"
#filesystem_size = "5G"

# lilik preferred distro
#distro = "debian"
#release = "jessie"

# our host
#backing_store = "lvm"
#filesystem_type = "ext4"
#
#
#lxc_create_options = {
#    "release": release,
#    "name": container_name,
#    "lvname": logical_volume_name,
#    "vgname": lvm_volume_group,
#    "fstype": filesystem_type,
#    "fssize": filesystem_size,
#}
#
#container = lxc.Container(container_name)
#container.create(distro, args=lxc_create_options)
#container.start()

#---
#- hosts: mcfly
#  remote_user: root
#  tasks:
#    - name: create a lxc container
#      lxc_container:
#        name: gogs
#        backing_store: lvm
#        container_log: true
#        fs_size: 5G
#        fs_type: ext4
#        lv_name: vm_gogs
#        state: started
#        template: debian
#        template_options: --release jessie
#        vg_name: sysvg
#        container_command: apt-get update; apt-get install python

import lxc
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
        self.lvname = module.params['lv_name']
        self.vgname = module.params['vg_name']
        self.fstype = module.params['fs_type']
        self.fssize = module.params['fssize']
        

    def create_container(self):
        """
        Create a lxc.Container object and returns it
        """
        container_options = {
           'bdev': self.backing_store,
           'lvname': self.lvname,
           'vgname': self.vgname,
           'fstype': self.fstype,
           'fssize': self.fssize
        }

        container = lxc.Container(name = self.name)

        return container.create(
                    template = self.template,
                    args = container_options,
                    bdevtype=self.backing_store
               )
                                 
    def destroy_container(self):
        pass
                                   

def main():
    module = AnsibleModule(
        argument_spec = dict(
            backing_store = dict(
                                default='dir',
                                choices=['dir', 'lvm', 'loop', 'btrsf', 'overlayfs', 'zfs', type='str'],
            ),
            container_command = dict(
                                    required=False,
                                    type='str',
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
                        required=False,
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
                        default='ubuntu',
                        type='str',
            ),
            template_options = dict(required=False),
            vg_name = dict(
                        required=False,
                        default='lxc',
                        type='str',
            ),
        )
    )

    container = LilikContainer(module)

    result = {}
    result['name'] = container.name
    result['state'] = container.state

    if container.state == 'absent':

        # test wether the container is absent or not
        if container.name in lxc.list_containers():
            module.fail_json(changed=False)

        # the container has been removed
        else:
            module.exit_json(changed=True)

    elif container.state in ['started', 'stopped', 'restarted', 'frozen']:
        
        if container.name in lxc.list_containers():
            module.exit_json(changed=True)
        else:
            try:
                new_container = container.create_container()
                module.exit_json(changed=True)
            except Exception:
                module.fail_json(
                        changed=False,
                        msg='An excption was raised when creating the container'
                )
            

#    container.name not in lxc.list_containers():
#        module.fail_json(changed=False)


if __name__ == '__main__':
    main()
