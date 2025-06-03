# CLuster API Virtual Kubelet Slurm Integration

Imagine being able to use your on-prem Kubernete cluster to create a bare-metal SLURM cluster. Then imagine using Kuberenetes to seamlessly exchanging GPU nodes between Slurm and Kubernetes as demand required. This is actually possible now. 

This repository contains all the projects and configurations needed to make it possible,

Prerequisites:
- [Metal3 Developer Enviroment](https://github.com/metal3-io/metal3-dev-env)
- Virtual Kubelet Bootstrap Provider