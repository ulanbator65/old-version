
from VastClient import VastClient
from InstanceTable import InstanceTable

from VastInstanceRules import *
import constants as const
import input
import config


class TerminateMenu:

    def __init__(self, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast


    def instance_termination_menu(self, instance_table: InstanceTable):
#        managed_instances = instance_table.get_managed_instances()
        print("\nInstances Available for Termination:")
#        managed_instances.print_table()

        self.kill_selected_instance(instance_table)


    def purge_dead_instances(self, instances : InstanceTable):
        managed_instances = instances.get_managed_instances()
        print("\nInstances Available for Termination:")
        managed_instances.print_table()

        dead_instances = []

        for inst in managed_instances.instances:
            if VastInstanceRules.is_dead(inst.actual_status):

                print("\nIdentified dead instances for termination:")
                print(f"Instance ID: {inst.cid}")
                dead_instances.append(inst)

                confirm = input.get_choice("\nConfirm termination of all identified dead instances? (y/n): ").lower()

                if confirm.startswith('y'):
                    self.vast.kill_instance(inst.cid)
                else:
                    print("Operation cancelled.")

        if len(dead_instances) == 0:
            print("No dead instances identified for termination.")


    def kill_selected_instance(self, instance_table: InstanceTable):
        selected_row = input.get_choice(''"Enter the row number of the instance to kill: ")

        if selected_row == const.CH_EXIT:
            print("\nExit menu... ")
            return

        print("\nSelected Instance for Termination: ", selected_row)

        instance_id = instance_table.get_id_for_row(int(selected_row))
        if instance_id:
            print(f"Instance ID: {instance_id}")
            confirm = input.get_choice("\nConfirm termination of selected instance? (y/n): ").lower()

            if confirm.startswith('y'):
                self.vast.kill_instance(instance_id)
            else:
                 print("Operation cancelled.")
        else:
            print("No valid instances selected for termination.")

