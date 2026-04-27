// Jenkins Scripted Pipeline — FastAPI GitHub Gists App
// Stages: Build → Test → Push → Deploy
// Requires: Docker on agent, credentials 'docker-registry-creds' and 'deploy-ssh-creds'

def IMAGE_NAME  = 'fastapi-gists'
def REGISTRY    = 'your-registry.example.com'          // e.g. docker.io/youruser
def DEPLOY_HOST = 'deploy.example.com'
def DEPLOY_USER = 'ubuntu'
def DEPLOY_PORT = '8080'
def CONTAINER   = 'fastapi-gists-app'

def imageTag    = ''    // set after SCM checkout
def fullImage   = ''    // REGISTRY/IMAGE_NAME:TAG

node {

    try {

        // ─────────────────────────────────────────────
        // STAGE 1 — Checkout
        // ─────────────────────────────────────────────
        stage('Checkout') {
            checkout scm
            imageTag  = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
            fullImage = "${REGISTRY}/${IMAGE_NAME}:${imageTag}"
            echo "Building image: ${fullImage}"
        }

        // ─────────────────────────────────────────────
        // STAGE 2 — Build Docker image
        // ─────────────────────────────────────────────
        stage('Build') {
            sh "docker build -t ${fullImage} -t ${REGISTRY}/${IMAGE_NAME}:latest ."
        }

        // ─────────────────────────────────────────────
        // STAGE 3 — Test (run pytest inside container)
        // ─────────────────────────────────────────────
        stage('Test') {
            // Spin up a temporary container with pytest installed and run tests.
            // The test image reuses the build image so behaviour matches production.
            sh """
                docker run --rm \
                    --name ${CONTAINER}-test-${imageTag} \
                    --entrypoint "" \
                    ${fullImage} \
                    sh -c "pip install --quiet pytest pytest-asyncio anyio httpx && pytest test_main.py -v"
            """
        }

        // ─────────────────────────────────────────────
        // STAGE 4 — Push to registry
        // ─────────────────────────────────────────────
        stage('Push') {
            withCredentials([usernamePassword(
                credentialsId: 'docker-registry-creds',
                usernameVariable: 'REG_USER',
                passwordVariable: 'REG_PASS'
            )]) {
                sh "echo '${REG_PASS}' | docker login ${REGISTRY} -u '${REG_USER}' --password-stdin"
                sh "docker push ${fullImage}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 5 — Deploy to remote host via SSH
        //   • Pulls the new image
        //   • Stops + removes the old container (if running)
        //   • Starts a fresh container on DEPLOY_PORT
        // ─────────────────────────────────────────────
        stage('Deploy') {
            withCredentials([sshUserPrivateKey(
                credentialsId: 'deploy-ssh-creds',
                keyFileVariable: 'SSH_KEY',
                usernameVariable: 'SSH_USER'
            )]) {
                def deployScript = """
                    docker pull ${fullImage} && \
                    docker stop ${CONTAINER} 2>/dev/null || true && \
                    docker rm   ${CONTAINER} 2>/dev/null || true && \
                    docker run -d \
                        --name ${CONTAINER} \
                        --restart unless-stopped \
                        -p ${DEPLOY_PORT}:8080 \
                        ${fullImage}
                """.stripIndent().trim()

                sh """
                    ssh -o StrictHostKeyChecking=no \
                        -i \${SSH_KEY} \
                        ${DEPLOY_USER}@${DEPLOY_HOST} \
                        '${deployScript}'
                """
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 6 — Smoke test (health endpoint)
        // ─────────────────────────────────────────────
        stage('Smoke Test') {
            retry(5) {
                sleep 5
                sh "curl --fail --silent http://${DEPLOY_HOST}:${DEPLOY_PORT}/health"
            }
            echo "Deployment healthy at http://${DEPLOY_HOST}:${DEPLOY_PORT}"
        }

    } catch (err) {
        currentBuild.result = 'FAILURE'
        echo "Pipeline failed: ${err}"
        throw err

    } finally {
        // Always clean up local images to avoid disk bloat on the agent
        sh "docker rmi ${fullImage} ${REGISTRY}/${IMAGE_NAME}:latest 2>/dev/null || true"
        // Logout so credentials are not cached on the agent
        sh "docker logout ${REGISTRY} 2>/dev/null || true"
    }
}
