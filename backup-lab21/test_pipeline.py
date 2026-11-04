"""Run Jenkinsfile shell snippets with fake tools; no Docker/cluster access."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


PIPELINE = Path(__file__).with_name('Jenkinsfile').read_text()
# The template uses literal Groovy strings; decode its newline escapes and continuations.
SHELLS = re.findall(r"(?:sh\s+|script:\s*)'''(.*?)'''|\bsh '(.*?)'", PIPELINE, re.S)
SHELLS = [(multi or single).replace('\\\\', '\\').replace('\\\n', '')
          for multi, single in SHELLS]

MOCK = '''#!/usr/bin/env python3
import os, pathlib, sys
tool = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as log:
    log.write(tool + ' ' + ' '.join(args) + '\\n')
failure = os.environ.get('FAIL', '')
if tool == 'docker':
    if args[0] == 'login':
        sys.stdin.read()
        pathlib.Path(os.environ['DOCKER_CONFIG'], 'config.json').write_text('secret')
    if failure == 'push' and args[0] == 'push': sys.exit(7)
    if failure == 'image-build' and args[0] == 'build': sys.exit(6)
    if failure == 'cleanup' and args[:2] == ['image', 'rm']: sys.exit(11)
elif tool == 'trivy':
    if failure == 'scan': sys.exit(8)
    pathlib.Path(args[args.index('--output') + 1]).write_text('CRITICAL: example finding')
elif tool == 'kubectl':
    print('image: ' + os.environ['IMAGE'])
elif tool == 'ssh':
    command = args[-1]
    if command.startswith('mktemp '): print('/tmp/jenkins-deploy.abc123')
    if failure == 'rollout' and 'rollout status' in command: sys.exit(9)
elif tool == 'scp' and failure == 'copy':
    sys.exit(10)
'''


class PipelineShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        for tool in ('docker', 'trivy', 'kubectl', 'ssh', 'scp'):
            path = bin_dir / tool
            path.write_text(MOCK)
            path.chmod(0o755)
        self.env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}',
                        WORKSPACE=str(self.root), CALLS=str(self.root / 'calls'),
                        SOURCE_REPO='https://example.com/app.git', BUILD_COMMAND='true',
                        DOCKERHUB_REPO='example/app', IMAGE='example/app:42',
                        CONTAINER_NAME='app', DEPLOYMENT_NAME='app', KUBE_NAMESPACE='default',
                        SSH_HOST='control.example.com', SSH_USER='deploy',
                        DOCKERHUB_USER='example', DOCKERHUB_TOKEN='test-token',
                        KNOWN_HOSTS=str(self.root / 'known_hosts'), DOCKERFILE='Dockerfile',
                        APP_DIR='.', DEPLOYMENT_FILE='deployment.yaml')
        (self.root / 'source').mkdir()
        (self.root / 'source/deployment.yaml').write_text('original manifest')
        (self.root / 'artifacts').mkdir()

    def run_shell(self, index, failure=''):
        return subprocess.run(['sh', '-eu', '-c', SHELLS[index]], cwd=self.root,
                              env=dict(self.env, FAIL=failure), capture_output=True, text=True)

    def test_shell_syntax(self):
        self.assertEqual(len(SHELLS), 9)
        for script in SHELLS:
            result = subprocess.run(['sh', '-n'], input=script, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_success_with_vulnerability_findings(self):
        for index in range(len(SHELLS)):
            result = self.run_shell(index)
            self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / 'calls').read_text()
        self.assertIn('docker push example/app:42', calls)
        self.assertIn('docker image rm example/app:42', calls)
        self.assertIn('StrictHostKeyChecking=yes', calls)
        self.assertIn('rollout status deployment/app --timeout=300s', calls)
        self.assertIn('rm -rf -- /tmp/jenkins-deploy.abc123', calls)
        self.assertIn('CRITICAL', (self.root / 'artifacts/trivy-report.txt').read_text())
        self.assertIn('example/app:42', (self.root / 'artifacts/deployment.yaml').read_text())
        self.assertEqual((self.root / 'source/deployment.yaml').read_text(), 'original manifest')
        self.assertFalse((self.root / '.docker-auth').exists())

    def test_build_failure(self):
        self.env['BUILD_COMMAND'] = 'false'
        self.assertNotEqual(self.run_shell(1).returncode, 0)

    def test_scan_execution_failure(self):
        self.assertEqual(self.run_shell(3, 'scan').returncode, 8)

    def test_image_build_failure(self):
        self.assertEqual(self.run_shell(2, 'image-build').returncode, 6)

    def test_cleanup_failure_does_not_fail_post_action(self):
        auth = self.root / '.docker-auth'
        auth.mkdir()
        (auth / 'config.json').write_text('secret')
        self.assertEqual(self.run_shell(8, 'cleanup').returncode, 0)
        self.assertFalse(auth.exists())

    def test_push_failure_removes_credentials(self):
        self.assertEqual(self.run_shell(4, 'push').returncode, 7)
        self.assertFalse((self.root / '.docker-auth').exists())

    def test_deployment_failures_cleanup_remote_files(self):
        for failure, code in [('rollout', 9), ('copy', 10)]:
            with self.subTest(failure=failure):
                self.assertEqual(self.run_shell(7, failure).returncode, code)
                self.assertIn('rm -rf -- /tmp/jenkins-deploy.abc123',
                              (self.root / 'calls').read_text())

    def test_reject_unconfigured_template(self):
        self.env['SOURCE_REPO'] = 'REPLACE_WITH_GIT_URL'
        self.assertNotEqual(self.run_shell(0).returncode, 0)


if __name__ == '__main__':
    unittest.main()
