"""Build a self-contained local service for the host platform."""
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
target=subprocess.check_output(['rustc','-vV'],text=True).split('host: ')[1].splitlines()[0]
subprocess.run([sys.executable,'-m','PyInstaller','--onefile','--name','cc-service','--distpath',str(root/'service/dist'),'--workpath',str(root/'service/build'),'--specpath',str(root/'service'),'--noconfirm',str(root/'service/main.py')],check=True)
extension='.exe' if sys.platform=='win32' else ''
out=root/'src-tauri/binaries'/f'cc-service-{target}{extension}'
out.parent.mkdir(exist_ok=True)
shutil.copy2(root/'service/dist'/('cc-service'+extension),out)
print(f'Packaged local service: {out.name}')
