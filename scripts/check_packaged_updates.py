"""Exercise public HTTPS from the frozen helper; never download/run an installer."""
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text())['version']
helper=root/'service/dist'/('cc-service.exe' if sys.platform=='win32' else 'cc-service')
request=dict(action='update_check',args=dict(_version=version,_target='windows-x64' if sys.platform=='win32' else 'macos'))
result=subprocess.run([str(helper)],input=json.dumps(request),text=True,capture_output=True,timeout=45,check=True)
reply=json.loads(result.stdout)
if not reply.get('ok') and 'HTTP Error 403: rate limit exceeded' in reply.get('error',''):
    # Hosted runners share public egress addresses. An authenticated TLS HTTP
    # response proves the frozen certificate bundle worked; do not confuse the
    # runner's exhausted anonymous API quota with a broken packaged dependency.
    print('Frozen helper reached GitHub over verified HTTPS; shared runner API quota exhausted. Release parsing/download guards are covered by tests.')
    sys.exit(0)
assert reply.get('ok'),reply
assert reply['result']['current']==version,reply
assert reply['result']['latest'],reply
print('Frozen helper verified public GitHub release HTTPS:',reply['result']['latest'])
