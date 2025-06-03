import os
from kubernetes import client, config
import csv
import pandas as pd
import paramiko

output_file = 'de_custom_image_sh.csv' 

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


deprovision_start = []
deprovision_end = []
names = []

# Print information about each BareMetalHost
print("Bare Metal Hosts in namespace '{}':".format(namespace))
for host in bare_metal_hosts.get('items', []):
    name = host['metadata']['name']

    status = host.get('status', {})
    start_prov = status['operationHistory']['deprovision']['start']
    end_prov = status['operationHistory']['deprovision']['end']

    if start_prov == None or end_prov == None:
        print(f"Name: {name} somethin null")
        continue

    print(f"Name: {name} done")
    names.append(name)
    deprovision_start.append(start_prov)
    deprovision_end.append(end_prov)


with open(output_file, "w+") as file:
    file.write("name,deprovision_start,deprovision_end")

df = pd.read_csv(output_file)
df["name"] = names
df["deprovision_start"] = deprovision_start
df["deprovision_end"] = deprovision_end

df.to_csv(output_file, index=False)