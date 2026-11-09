// Shared library step: point the manifest at the new image and push the change to GitHub.
// Argo CD (auto-sync) detects the commit and applies it to the cluster.
def call(String imageName, String manifestPath, String gitCredentialsId, String repoUrl, String branch) {
    def image = "${imageName}:${env.BUILD_NUMBER}"

    echo "Updating ${manifestPath} to ${image}"
    def original = readFile(manifestPath)
    def pattern = /(?m)^([ \t]*(?:-[ \t]*)?image:[ \t]*)/ + java.util.regex.Pattern.quote(imageName) + /.*/
    def updated = original.replaceAll(pattern, "\$1${image}")

    if (!updated.contains("image: ${image}")) {
        error "image not updated in ${manifestPath}"
    }
    writeFile(file: manifestPath, text: updated)

    withCredentials([usernamePassword(
        credentialsId: gitCredentialsId,
        usernameVariable: 'GIT_USER',
        passwordVariable: 'GIT_TOKEN'
    )]) {
        withEnv(["MANIFEST_PATH=${manifestPath}", "IMAGE=${image}", "BRANCH=${branch}", "REPO_URL=${repoUrl}"]) {
            sh '''
                git config user.name "Jenkins CI"
                git config user.email "jenkins-ci@users.noreply.github.com"

                if git diff --quiet -- "$MANIFEST_PATH"; then
                    echo "Manifest already references $IMAGE, nothing to push"
                    exit 0
                fi

                git checkout -B "$BRANCH"
                git add -- "$MANIFEST_PATH"
                git commit -m "Update $MANIFEST_PATH image to $IMAGE [ci skip]"

                git -c credential.helper= -c 'credential.helper=!f() { echo username=$GIT_USER; echo password=$GIT_TOKEN; }; f' pull --rebase "https://$REPO_URL" "$BRANCH"
                git -c credential.helper= -c 'credential.helper=!f() { echo username=$GIT_USER; echo password=$GIT_TOKEN; }; f' push "https://$REPO_URL" "HEAD:$BRANCH"
            '''
        }
    }
    echo "Manifest step done for ${image}; Argo CD syncs any new commit on ${branch}"
}
