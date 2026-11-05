def call(String imageName, String manifestPath, String kubeCredentialsId, String namespace) {
    def image = "${imageName}:${env.BUILD_NUMBER}"

    withCredentials([file(credentialsId: kubeCredentialsId, variable: 'KUBECONFIG')]) {
        echo "Updating ${manifestPath} to ${image}"

        sh """
            sed -i 's|^\\([[:space:]]*\\(-[[:space:]]*\\)\\?image:[[:space:]]*\\)${imageName}.*|\\1${image}|' '${manifestPath}'
            grep -Eq '^[[:space:]]*(-[[:space:]]*)?image:[[:space:]]*${image}[[:space:]]*\$' '${manifestPath}' || {
                echo "image not updated"
                exit 1
            }
        """
        sh "kubectl apply -f '${manifestPath}' -n '${namespace}'"
        sh "kubectl rollout status -f '${manifestPath}' -n '${namespace}' --timeout=180s"
    }
}