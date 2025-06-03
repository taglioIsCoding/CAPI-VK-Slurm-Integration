# Data extraction steps 

1. Provision the cluster 
``` 
kubectl scale machinedeployment <machine-deployment-name> -n metal3 --replicas <number-of replicas>
```

2. Get the provision time from nodes

- If the nodes are slurm nodes:
```
python3 scraping_slurm.py
```
- If the nodes are kubernetes nodes:
```
python3 scraping_kubernetes.py
```

3. Deprovision the cluster
``` 
kubectl scale machinedeployment <machine-deployment-name> -n metal3 --replicas 0
```

4. Get deprovision times 
```
python3 scraping_deprovision.py
```

5. Get the final report
```
python3 merge_files.py
```
