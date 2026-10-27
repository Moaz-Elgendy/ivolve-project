# Lab 11 — Resource Quota

Create the `ivolve` namespace, cap it at 3 pods with a `ResourceQuota`, and prove the limit is enforced.

| Item | Value |
|---|---|
| Namespace | `ivolve` |
| ResourceQuota | `ivolvequota` |
| Hard limit | `pods: "3"` |

The screenshots use `k` as an alias for `kubectl`.

## Step 1 — Create the namespace

```bash
kubectl create namespace ivolve
kubectl get namespaces
```

![Creating the ivolve namespace and listing namespaces](Screenshot%202026-10-27%20193905.png)

The namespace is `Active`. All quota-scoped work stays inside `ivolve`.

## Step 2 — Generate the quota manifest

```bash
kubectl create quota ivolveQuota --hard=pods=3 -n ivolve --dry-run=client -o yaml > quota-ivolve.yaml
cat quota-ivolve.yaml
```

![Dry-run quota saved to quota-ivolve.yaml and displayed](Screenshot%202026-10-27%20194703.png)

The manifest contains `spec.hard.pods: "3"`. The dry run generates the file locally without creating anything on the cluster.

## Step 3 — Apply the quota

```bash
kubectl create quota ivolvequota --hard=pods=3 -n ivolve
```

![Creating the quota, resourcequota/ivolvequota created](Screenshot%202026-10-27%20195030.png)

Expected output: `resourcequota/ivolvequota created`.

The applied name is lowercase (`ivolvequota`) because Kubernetes names must follow DNS-1123.

## Step 4 — Verify the quota

```bash
kubectl describe namespaces ivolve
```

![describe namespace showing ivolvequota used 0, hard 3](Screenshot%202026-10-27%20195104.png)

The `Resource Quotas` block shows `pods  0  3` (used / hard) and `No LimitRange resource`.

## Step 5 — Test the limit

```bash
kubectl run --image nginx ivolve-pod1 -n ivolve
kubectl run --image nginx ivolve-pod2 -n ivolve
kubectl run --image nginx ivolve-pod3 -n ivolve
kubectl run --image nginx ivolve-pod4 -n ivolve
```

![Three pods created, fourth rejected for exceeding the quota](Screenshot%202026-10-27%20195307.png)

The first three pods are admitted. The fourth fails at admission:

```
Error from server (Forbidden): pods "ivolve-pod4" is forbidden: exceeded quota: ivolvequota,
requested: pods=1, used: pods=3, limited: pods=3
```

The quota is enforced by the API server, so the fourth pod object is never created.

The three pods show `Pending` — consistent with the Lab 10 taint still on `k8s-worker`, which none of these pods tolerate. Pending pods still count against the quota.

## Step 6 — Confirm namespace scoping

```bash
kubectl get pods
kubectl get pods -n ivolve
```

![get pods in default namespace finds nothing, get pods -n ivolve lists three pods](Screenshot%202026-10-27%20195307.png)

`No resources found in default namespace` — the quota and pods exist only in `ivolve`, which must be passed with `-n`.

## Result

The `ivolve` namespace accepts a maximum of 3 pods. Attempts beyond that are rejected by the API server with `exceeded quota`, confirming the `ResourceQuota` is active.

## Files

| File | Contents |
|---|---|
| `quota-ivolve.yaml` | `ResourceQuota` manifest generated with `--dry-run=client` |

## Cleanup

```bash
kubectl delete namespace ivolve
```

Deleting the namespace removes the quota and every pod inside it.
