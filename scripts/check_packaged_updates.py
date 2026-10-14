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
assert reply.get('ok'),reply
assert reply['result']['current']==version,reply
assert reply['result']['latest'],reply
print('Frozen helper verified public GitHub release HTTPS:',reply['result']['latest'])
