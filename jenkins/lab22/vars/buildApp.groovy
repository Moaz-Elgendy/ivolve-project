def call(String imageName, String dockerCredsId, String contextDir = '.') {
    def image = "${imageName}:${env.BUILD_NUMBER}"

    echo "Building ${image}"
    sh "docker build -t ${image} ${contextDir}"

    echo "Scanning ${image} for vulnerabilities using trivy (non-blocking)"
    sh """
        trivy image --exit-code 0 --severity HIGH,CRITICAL --skip-java-db-update \
        --ignore-unfixed --no-progress --cache-dir /var/lib/jenkins/trivy-cache \
        --format template --template "@/usr/local/share/trivy/templates/html.tpl" \
        --output trivy-report.html ${image}
    """
    archiveArtifacts artifacts: 'trivy-report.html', allowEmptyArchive: true

    withCredentials([usernamePassword(
        credentialsId: dockerCredsId,
        usernameVariable: 'DOCKER_USER',
        passwordVariable: 'DOCKER_PASS'
    )]) {
        sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
        sh "docker push ${image}"
    }

    sh "docker rmi ${image} || true"
    echo "Pushed ${image} and removed it from local docker cache"
}
