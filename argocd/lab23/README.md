# Lab 23: GitOps Workflow with Jenkins and Argo CD

## Objective

Move deployment out of Jenkins and into Git. Jenkins builds and publishes the application image, then commits the new image tag to the GitHub repository. Argo CD watches that repository and applies the change to the `ivolve` namespace automatically.

1. Install Argo CD in the Kubernetes cluster and log in to its UI.
2. Connect Argo CD to the GitHub repository.
3. Create an Argo CD Application named `ivolve` that watches the manifest directory.
4. Enable automatic synchronization (auto-sync, self-heal, prune).
5. Change the Jenkins `DeployOnK8s` step so it pushes the updated manifest to GitHub instead of calling `kubectl apply`.
6. Trigger the pipeline with a push, build and publish a new image, and confirm Argo CD detects and syncs the change.

---

## Flow

```text
git push (main)
   │  GitHub webhook (githubPush trigger)
   ▼
Jenkins pipeline
   ├── Checkout              built-in agent
   ├── BuildImage            docker build → Trivy scan → docker push mk0230/application-ivolve:<BUILD_NUMBER>
   └── UpdateManifestInGit   sed image line in kubernetes/lab15/app-deployment-ivolve.yaml
                             git commit "[ci skip]" → git pull --rebase → git push to main
   │
   ▼
GitHub (main) ── Argo CD polls/receives change ── auto-sync ──► Deployment ivolve-app in namespace ivolve
```

Jenkins no longer connects to the cluster. The `k8s-agent` node and the `jenkins-kubeconfig` credential are not used by this pipeline.

---

## Directory Structure

```text
lab23/
├── Jenkinsfile                          # Pipeline: Checkout → BuildImage → UpdateManifestInGit
├── buildApp.groovy                      # Shared library step: build, Trivy scan, push image
├── pushGithub.groovy                    # Shared library step: update image in manifest and push to GitHub
└── Screenshot 2026-11-08 224829.png     # Argo CD UI: ivolve application Synced and Sync OK
```

---

## Part 1: Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deployment/argocd-server
```

Open the UI with a port-forward (or a NodePort, as used in the lab screenshot at port `8040`):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Get the initial admin password and log in at `https://localhost:8080` with user `admin`:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

Log in from the CLI if needed:

```bash
argocd login localhost:8080 --username admin --insecure
```

---

## Part 2: Connect Argo CD to GitHub

Repository: `https://github.com/Moaz-Elgendy/ivolve-project.git`

In the UI: **Settings → Repositories → Connect Repo**, choose HTTPS or SSH, and provide the URL. Or from the CLI:

```bash
argocd repo add git@github.com:Moaz-Elgendy/ivolve-project.git --ssh-private-key-path ~/.ssh/id_ed25519
```

The repository must show `Successful` connection status before the application is created.

---

## Part 3: Create the `ivolve` Application

Watch the manifest directory that holds the Deployment Jenkins updates. In this repo that is `kubernetes/lab15`, which contains `app-deployment-ivolve.yaml`.

```bash
argocd app create ivolve \
  --repo https://github.com/Moaz-Elgendy/ivolve-project.git \
  --path kubernetes/lab15 \
  --revision main \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace ivolve \
  --sync-policy automated \
  --self-heal \
  --auto-prune
```

Equivalent settings in the UI: **Applications → New App** with Application Name `ivolve`, Project `default`, Sync Policy `Automatic` (with `Prune Resources` and `Self Heal` enabled), Repository URL, Revision `main`, Path `kubernetes/lab15`, Cluster `https://kubernetes.default.svc`, Namespace `ivolve`.

The **Automatic** policy is what makes Argo CD apply changes detected in Git without a manual Sync. `Self Heal` reverts manual `kubectl` edits to the live object. `Prune` deletes resources removed from Git.

---

## Part 4: Modify the Jenkins Pipeline

### Jenkinsfile

[Jenkinsfile](Jenkinsfile) changes from the Lab 22 version:

- `triggers { githubPush() }` runs the pipeline on every push to the repository.
- The `DeployKubernetes` stage on `k8s-agent` is replaced by `UpdateManifestInGit` on the `built-in` agent.
- `GITHUB_CREDENTIALS`, `GIT_REPO_URL` and `GIT_BRANCH` are added to `environment`.
- Every stage has `when { not { changelog '.*\\[ci skip\\].*' } }`. Jenkins' own manifest commit contains `[ci skip]`, so it does not start another build (no loop).

### pushGithub.groovy (shared library)

[pushGithub.groovy](pushGithub.groovy) now does three things:

1. Replaces the `image:` line of the target Deployment with `mk0230/application-ivolve:<BUILD_NUMBER>`. The update uses a regular expression in Groovy, and the step fails if the new tag is not in the file.
2. Commits the change as `Jenkins CI` with the message `Update <manifest> image to <image> [ci skip]`. If the manifest is already up to date, it exits without a commit.
3. Runs `git pull --rebase` and `git push` to `main` over HTTPS. The token comes from the Jenkins credential, so it is never written into the URL or the logs.

It no longer runs `kubectl apply` or `kubectl rollout status`. Argo CD performs the rollout.

### Jenkins prerequisites

| Item | Name / setting |
|---|---|
| Credential (Username + Personal Access Token with `repo` scope) | `github-credentials` |
| Credential (Docker Hub) | `docker-hub` (unchanged) |
| Global Pipeline Library | `shared-lib` (contains `vars/buildApp.groovy` and `vars/pushGithub.groovy`) |
| Plugin | GitHub plugin (provides `githubPush()`) |
| GitHub webhook | `http://<jenkins-host>:<port>/github-webhook/` on the repository, push event |

Update the shared library repository with the new `pushGithub.groovy` so Jenkins uses the same logic as this folder.

---

## Part 5: Test the GitOps Loop

1. Make a change that should trigger a build (for example, a small change under `docker/lab8`) and push it to `main`.
2. Jenkins starts the pipeline from the webhook. Confirm the stages `Checkout`, `BuildImage` and `UpdateManifestInGit` pass.
3. Confirm Docker Hub has the new tag `mk0230/application-ivolve:<BUILD_NUMBER>`.
4. Confirm GitHub has a new commit by `Jenkins CI`, with the message `Update kubernetes/lab15/app-deployment-ivolve.yaml image to mk0230/application-ivolve:<BUILD_NUMBER> [ci skip]`, and that only the `image:` line changed:

   ```bash
   git log -1 --stat origin/main
   git show origin/main -- kubernetes/lab15/app-deployment-ivolve.yaml
   ```

5. Confirm the commit does not start a second Jenkins build.
6. Confirm Argo CD detects the change. The application goes to `OutOfSync` and then back to `Synced` without a manual sync:

   ```bash
   argocd app get ivolve
   kubectl get deployment ivolve-app -n ivolve -o jsonpath="{.spec.template.spec.containers[0].image}"; echo
   ```

   Expected: `Sync Status: Synced to main (<commit>)` and the image shows the new `<BUILD_NUMBER>` tag.

### Result

The screenshot [Screenshot 2026-11-08 224829.png](Screenshot%202026-11-08%20224829.png) shows the `ivolve` application in the Argo CD UI (v3.6.1):

- **Sync Status:** `Synced to main (6a51736)`, with `Auto sync is enabled`.
- **Last Sync:** `Sync OK` to `6a51736`, by the commit author in the repository.
- **Resources:** 12 `Synced`, 0 `OutOfSync`.
- **App Health:** `Degraded`, caused by `apps/Deployment:ivolve/ivolve-app`. A new ReplicaSet (`rev:13`) is still starting: its pod shows `init:0/1`, which is the `init-mysql` init container waiting for the database. The sync itself succeeded. Health reaches `Healthy` when the new pod passes its init container and readiness check.

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Argo CD shows `Synced` but the image did not change | The Application path must match the file Jenkins edits (`kubernetes/lab15`). Run `argocd app get ivolve` and check `Path`. |
| Jenkins `UpdateManifestInGit` fails with `image not updated` | The `image:` line in the manifest must start with `mk0230/application-ivolve`. |
| `git push` is rejected | `github-credentials` must have push permission. Check that `main` is not protected against pushes from the token's user. |
| Pipeline loops on its own commits | The commit message must contain `[ci skip]`. Check `Update ... [ci skip]` in `git log`. |
| No build starts on push | Check the GitHub webhook delivery log and the Jenkins GitHub plugin configuration. |
| Application stays `Degraded` | `kubectl describe pod -n ivolve -l app=ivolve-app` and `kubectl logs -n ivolve <pod> -c init-mysql`. |
