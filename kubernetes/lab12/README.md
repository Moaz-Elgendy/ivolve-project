# Lab 12 — ConfigMaps and Secrets

Store non-sensitive configuration in a `ConfigMap` and credentials in a `Secret`, both in the `ivolve` namespace from Lab 11.

| Object | Name | Data |
|---|---|---|
| ConfigMap | `ivolve-cm` | `DB_HOST=ivolve`, `DB_USER=ivolve` |
| Secret | `ivolve-secret` | `DB_PASSWORD`, `MY_SQL_ROOT_PASSWORD` |

The screenshots use `k` as an alias for `kubectl`.

## Step 1 — Generate the ConfigMap manifest

```bash
kubectl create configmap ivolveCM -n ivolve \
  --from-literal=DB_HOST=ivolve \
  --from-literal=DB_USER=ivolve \
  --dry-run=client -o yaml > configmap-ivolve.yaml
```

![Dry-run ConfigMap saved to configmap-ivolve.yaml](Screenshot%202026-10-27%20211339.png)

The file is written locally; no object is created on the cluster.

## Step 2 — Apply the ConfigMap

The first apply used the same camelCase name and was rejected:

```bash
kubectl create configmap ivolveCM -n ivolve --from-literal=DB_HOST=ivolve --from-literal=DB_USER=ivolve
```

```
error: failed to create configmap: ConfigMap "ivolveCM" is invalid: metadata.name:
Invalid value: "ivolveCM": a lowercase RFC 1123 subdomain must consist of lower case
alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character
```

Names must be lowercase, so the ConfigMap was created as `ivolve-cm`:

```bash
kubectl create configmap ivolve-cm -n ivolve --from-literal=DB_HOST=ivolve --from-literal=DB_USER=ivolve
```

![Name validation error, then configmap/ivolve-cm created](Screenshot%202026-10-27%20211339.png)

Expected output: `configmap/ivolve-cm created`.

> `configmap-ivolve.yaml` still has the rejected `ivolveCM` name. Change `metadata.name` to `ivolve-cm` before using the file with `kubectl apply -f`.

## Step 3 — Generate and apply the Secret

Generate the manifest:

```bash
kubectl create secret generic ivolve-secret -n ivolve \
  --from-literal=MY_SQL_ROOT_PASSWORD=root \
  --from-literal=DB_PASSWORD=ivolve \
  --dry-run=client -o yaml > secrets-ivolve.yaml
```

![Secret dry-run saved to secrets-ivolve.yaml, then secret created](Screenshot%202026-10-27%20211900.png)

Apply it:

```bash
kubectl create secret generic ivolve-secret -n ivolve \
  --from-literal=MY_SQL_ROOT_PASSWORD=root \
  --from-literal=DB_PASSWORD=ivolve
```

Expected output: `secret/ivolve-secret created`.

`kubectl create secret` automatically base64-encodes the values in the manifest. For example `ivolve` becomes `aXZvbHZl` and `root` becomes `cm9vdA==`. This is encoding, not encryption — the manifest should not hold real production credentials.

## Result

Both objects exist in `ivolve`:

- The ConfigMap `ivolve-cm` holds plain-text `DB_HOST` and `DB_USER` values.
- The Secret `ivolve-secret` holds base64-encoded `DB_PASSWORD` and `MY_SQL_ROOT_PASSWORD` values.

Applications consume them with `envFrom`/`valueFrom` (`configMapKeyRef`, `secretKeyRef`) or by mounting them as volumes.

## Files

| File | Contents |
|---|---|
| `configmap-ivolve.yaml` | ConfigMap manifest generated with `--dry-run=client` (name still `ivolveCM`, fix before applying) |
| `secrets-ivolve.yaml` | Secret manifest with base64-encoded data |

## Cleanup

```bash
kubectl delete configmap ivolve-cm -n ivolve
kubectl delete secret ivolve-secret -n ivolve
```
