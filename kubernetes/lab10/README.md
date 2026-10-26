# Lab 10 — Taints, Tolerations and Node Labels

Dedicate the worker node `k8s-worker` to a specific workload using a taint, then identify it with a label for targeted scheduling.

| Item | Value |
|---|---|
| Cluster | `k8s-cp` (control plane), `k8s-worker` (worker), Kubernetes v1.35.9 |
| Taint | `workload=ivolveApp:NoSchedule` |
| Label | `project=ivolve` |

The screenshots use `k` as an alias for `kubectl`.

## Step 1 — Check the worker node

```bash
kubectl get nodes
```

![kubectl get nodes showing k8s-cp and k8s-worker Ready](Screenshot%202026-10-26%20203618.png)

Both nodes are `Ready`. The same screenshot previews the taint with `--dry-run=client -o yaml`, confirming the exact taint object before it is applied.

## Step 2 — Apply the taint

```bash
kubectl taint node k8s-worker workload=ivolveApp:NoSchedule
```

![Applying the taint, node/k8s-worker tainted](Screenshot%202026-10-26%20203952.png)

Expected output: `node/k8s-worker tainted`.

`NoSchedule` means the scheduler will not place new pods on this node unless their pod spec has a matching toleration. Pods already running are not evicted.

## Step 3 — Label the worker node

Dry-run preview, showing the label added to the node's existing labels:

```bash
kubectl label node k8s-worker project=ivolve --dry-run=client -o yaml | grep -iA 10 labels
```

![Dry-run showing project=ivolve in the labels block](Screenshot%202026-10-26%20205243.png)

Apply the label:

```bash
kubectl label node k8s-worker project=ivolve
```

![Applying the label, node/k8s-worker labeled](Screenshot%202026-10-26%20205325.png)

Expected output: `node/k8s-worker labeled`.

## Step 4 — Verify the taint and label

**Taint check** with `kubectl describe node`:

```bash
kubectl describe node k8s-worker
```

![describe node showing Taints workload=ivolveApp:NoSchedule and label project=ivolve](Screenshot%202026-10-26%20205503.png)

The output shows `Taints: workload=ivolveApp:NoSchedule` and the label `project=ivolve` on the same node.

**Label check** with `kubectl get nodes --show-labels`:

```bash
kubectl get nodes --show-labels | grep k8s-worker
```

![get nodes --show-labels showing project=ivolve on k8s-worker](Screenshot%202026-10-26%20205633.png)

The label list ends with `project=ivolve`, confirming the label is set on the node.

## Result

The worker node is tainted with `workload=ivolveApp:NoSchedule` and labeled `project=ivolve`. Only pods that tolerate the taint can be scheduled there, and the label makes the node selectable with `nodeSelector` or `nodeAffinity`.

## Reference — pod that tolerates the taint

Not captured in the screenshots; shown for completeness.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tolerated-pod
spec:
  nodeSelector:
    project: ivolve
  tolerations:
    - key: workload
      operator: Equal
      value: ivolveApp
      effect: NoSchedule
  containers:
    - name: app
      image: nginx:stable
```

Without the `tolerations` block, the same pod stays `Pending` because the worker taint is not tolerated.

## Files

| File | Contents |
|---|---|
| `taint-worker.yaml` | Exported `k8s-worker` node manifest with the taint |
| `label-worker.yaml` | Exported `k8s-worker` node manifest with the taint and the label |

## Cleanup

```bash
kubectl taint node k8s-worker workload=ivolveApp:NoSchedule-
kubectl label node k8s-worker project-
```
