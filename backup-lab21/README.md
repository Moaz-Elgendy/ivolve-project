# Lab 21: Jenkins deployment pipeline

Edit the settings at the top of `Jenkinsfile` before running it. The image is
`DOCKERHUB_REPO:BUILD_NUMBER`, for example `yourname/app:12`. Numbers belong to
the Jenkins job; failed builds consume numbers too. Use one publishing job per
Docker Hub repository to avoid tag collisions.

## Configuration

| Setting | Meaning |
| --- | --- |
| `SOURCE_REPO`, `SOURCE_BRANCH` | Application Git URL and branch; default checkout assumes a public repo |
| `APP_DIR` | App directory and Docker build context, relative to repository root |
| `BUILD_COMMAND` | Shell command run inside the app directory, e.g. `mvn clean package` or `npm ci && npm run build` |
| `DOCKERFILE` | Dockerfile path relative to repository root, e.g. `backend/Dockerfile` |
| `DOCKERHUB_REPO` | Lowercase Docker Hub namespace/repository, e.g. `yourname/app` |
| `DEPLOYMENT_FILE` | Repository-relative path to a single Kubernetes Deployment manifest |
| `CONTAINER_NAME`, `DEPLOYMENT_NAME` | Existing container name and Deployment metadata name in that manifest |
| `KUBE_NAMESPACE` | Existing destination namespace; must match any namespace declared in the manifest |
| `SSH_HOST`, `SSH_USER` | Control-plane hostname/IPv4 address and SSH user (port 22) |

The manifest is rendered into `artifacts/deployment.yaml`; the source manifest
is not edited or committed. The build command must produce what the Dockerfile
expects. Change the build command to `true` only if no separate app build is needed.

## Jenkins setup

Install Pipeline, Git, Credentials Binding, SSH Agent, and Timestamper plugins.
Use a trusted Linux agent with Git, Docker CLI and daemon access, Trivy (supporting
`--image-src docker`), kubectl, SSH/SCP, ssh-agent, and the app's build tools.
`agent any` assumes all eligible agents satisfy these requirements; set an agent
label if only one does. The agent needs access to Git, Docker Hub, Trivy databases,
and the control-plane SSH endpoint.

Create credentials with these IDs, or change the IDs in the Jenkinsfile:

- `dockerhub`: **Username with password**; Docker Hub username and access token
  with permission to push to the configured repository.
- `control-plane-ssh`: **SSH Username with private key**; a key authorized for
  `SSH_USER` on the control-plane node. Set `SSH_USER` to the credential's user.
- `control-plane-known-hosts`: **Secret file** containing the control-plane's
  verified SSH host key. Verify its fingerprint through a trusted channel before
  uploading it; host-key checking is never disabled.

The remote user must have a working default kubeconfig/context and permission to
apply the Deployment and watch its rollout. Provision the namespace first. For a
private Docker Hub repository, configure an image-pull secret in that namespace
and reference it in the manifest. Jenkins's Docker login does not authenticate
Kubernetes image pulls.

Create a Pipeline job using this Jenkinsfile (script path
`jenkins/lab21/Jenkinsfile` when loading it from this repository). A private
application repo additionally needs a Git credential and `credentialsId` on the
checkout step. Treat this job and its source/build command as trusted code.

## Behavior and checks

Stages: checkout → app build → image build → Trivy scan → push → local image
deletion → manifest rendering → SSH deployment and rollout wait (five minutes).
Trivy findings are informational; execution errors stop the pipeline. Reports
and rendered manifests are archived even on failure when available. Post actions
log success/failure and retry local cleanup. No broad Docker pruning is used.
SSH temporary files are removed on ordinary success/failure; agent loss or SSH
connectivity loss can prevent cleanup. Failed rollouts are not rolled back.

Run `python3 test_pipeline.py` for isolated shell syntax and mocked command checks.
These checks do not validate Jenkins's Declarative model or real infrastructure.
Before production use, validate with your Jenkins Declarative Pipeline linter and
run against a test namespace. Confirm the numbered tag in Docker Hub and the
Deployment, archived outputs, local image deletion, and failure behavior for
build, Trivy execution, push, and rollout errors.
