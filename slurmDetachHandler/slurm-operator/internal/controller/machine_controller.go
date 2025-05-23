/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	cluster "sigs.k8s.io/cluster-api/api/v1beta1"
)

// MachineReconciler reconciles a Machine object
type MachineReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=cluster.x-k8s.io.mydomain.com,resources=machines,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=cluster.x-k8s.io.mydomain.com,resources=machines/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=cluster.x-k8s.io.mydomain.com,resources=machines/finalizers,verbs=update

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the Machine object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.19.0/pkg/reconcile
func (r *MachineReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	machine := &cluster.Machine{}
	if err := r.Client.Get(ctx, req.NamespacedName, machine); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	if machine.Status.Phase == "Provisioning" && machine.Annotations == nil && strings.Contains(machine.ObjectMeta.Name, "slurm-worker") {
		logger.Info("Provision a machine")
		// Add annotation to wait the drainig before deprovisioning
		machine.Annotations = make(map[string]string)
		machine.Annotations["pre-drain.delete.hook.machine.cluster.x-k8s.io"] = "drain-slurm"

		err := r.Client.Update(context.TODO(), machine)
		if err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	if machine.ObjectMeta.DeletionTimestamp != nil && machine.Annotations != nil && strings.Contains(machine.ObjectMeta.Name, "slurm-worker") {
		logger.Info("Deprovisioning a machine")

		// HTTP request to detch node from the cluster
		regex := regexp.MustCompile(`[0-9]{1,3}\.[0-9]{1,3}\.[2]{3}\.[0-9]{1,3}`)
		var externalNicIndex int
		for i, nic := range machine.Status.Addresses {
			if regex.MatchString(nic.Address) {
				externalNicIndex = i
			}
		}
		node := machine.Status.Addresses[externalNicIndex].Address
		mode := "detach"
		url := fmt.Sprintf("http://%s:8090/%s", node, mode)
		resp, err := http.Get(url)

		if err != nil || resp.StatusCode != 200 {
			fmt.Println("Cannot detach")
			fmt.Println(err)
			return ctrl.Result{}, err
		}

		// Remove annotation to continue deprovisioning
		delete(machine.Annotations, "pre-drain.delete.hook.machine.cluster.x-k8s.io")
		err = r.Client.Update(context.TODO(), machine)
		if err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *MachineReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&cluster.Machine{}).
		Complete(r)
}
