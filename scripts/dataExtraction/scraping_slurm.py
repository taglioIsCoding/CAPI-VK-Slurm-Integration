import os
import re
from kubernetes import client, config
import csv
import paramiko
from datetime import datetime

output_file = 'custom_image_sh.csv' 

# Load kubeconfig
config.load_kube_config()

custom_objects_api = client.CustomObjectsApi()

# Define the group, version, and plural for BareMetalHost
group = "metal3.io"
version = "v1alpha1"
plural = "baremetalhosts"

# Specify the namespace (use 'default' or the namespace where Metal3 is installed)
namespace = 'metal3'

# Get all BareMetalHost resources in the specified namespace
bare_metal_hosts = custom_objects_api.list_namespaced_custom_object(
    group=group,
    version=version,
    namespace=namespace,
    plural=plural
)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
private_key = paramiko.RSAKey.from_private_key_file('ADD-YOUR-SSH-KEY')

file_exists = os.path.isfile(output_file)
with open(output_file, mode='a', newline='') as csv_file:
    fieldnames = ['name', 'provision_start', 'provision_end', 'kernel_start', 'kernel_end_boot', 'cloud_init_activate', 'cloud_init_start', 'cloud_init_end', 'deprovision_start', 'deprovision_end']

    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    # Write the header
    if not file_exists:
        writer.writeheader()

    start_address = "192.168.222."
    data = []

    # Print information about each BareMetalHost
    print("Bare Metal Hosts in namespace '{}':".format(namespace))
    for host in bare_metal_hosts.get('items', []):
        name = host['metadata']['name']
        status = host.get('status', {})
        start_prov = status['operationHistory']['provision']['start']
        end_prov = status['operationHistory']['provision']['end']

        address = start_address + str(20 + int(name[5:]))
        # Connect to the host using the private key
        try:
            ssh.connect(address, username="mik", pkey=private_key)
        except Exception as e:
            print(f"Connection error {name} skipped")
            continue

        # Execute the command
        stdin, stdout, stderr = ssh.exec_command("sudo cat /var/log/cloud-init-output.log | awk 'END{print}'")
        output = stdout.read().decode()

        parsed_date = datetime.strptime(output[37:68], "%a, %d %b %Y %H:%M:%S %z")
        cloud_init_end = parsed_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")

        stdin, stdout, stderr = ssh.exec_command("sudo cloud-init analyze boot")
        output = stdout.read().decode()
        date_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2})'
        date_strings = re.findall(date_pattern, output)

        if len(date_strings) != 4:
            print(f"Error reading {name} skipped")
            continue

        ssh.close()

        print(f"Name: {name} done")
        writer.writerow(
            {
                'name': name,
                'provision_start': start_prov,
                'provision_end': end_prov,
                'kernel_start': date_strings[0],
                'kernel_end_boot': date_strings[1], 
                'cloud_init_activate':  date_strings[2],
                'cloud_init_start':  date_strings[3], 
                'cloud_init_end': cloud_init_end
            }
        )

