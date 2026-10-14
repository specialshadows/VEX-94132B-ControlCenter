"""Local, one-request service. Never evaluates robot code or invokes a shell.

Tauri supplies trusted roots; the webview cannot supply native root/tool paths.
"""
import ast
import base64
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid

BUTTONS = ('R1', 'R2', 'L1', 'L2', 'Up', 'Down', 'Left', 'Right', 'X', 'B', 'A', 'Y')
DEFAULT_MAPPING = dict(zip(('intake', 'outtake', 'cascade_up', 'cascade_down', 'angle_up', 'angle_down', 'claw_in', 'claw_out', 'lower_reference', 'upper_reference'), ('R1','R2','L1','L2','Up','Down','X','B','A','Y')))
MOTORS = {'front_left':14,'back_left':13,'front_right':12,'back_right':11,'top_intake':8,'bottom_intake':20,'pulley_left':9,'pulley_right':2,'claw_rotate':4,'claw_activate':3}
LIMITS = {'DRIVE_SCALE':(0,1), 'TURN_SCALE':(0,1), 'DEADZONE':(0,30), 'INTAKE_SPEED':(0,100), 'PULLEY_SPEED':(0,100), 'CLAW_ROTATE_SPEED':(0,100), 'CLAW_ACTIVATE_SPEED':(0,100), 'CLAW_TORQUE_LIMIT':(0,35)}
FLAGS = tuple(k.upper()+'_REVERSED' for k in MOTORS) + ('PULLEY_ENABLED','REVERSE_DRIVE_ENABLED','DRIVE_FORWARD_REVERSED','TURN_REVERSED')

class Failure(Exception): pass

def digest(data): return hashlib.sha256(data).hexdigest()

def executable(name):
    found=shutil.which(name)
    if found: return found
    candidates=[Path('/opt/homebrew/bin')/name,Path('/usr/local/bin')/name]
    if os.name=='nt':
        program_files=Path(os.environ.get('ProgramFiles','C:/Program Files'))
        candidates += [program_files/'GitHub CLI/gh.exe' if name=='gh' else program_files/'Git/cmd/git.exe']
    return next((str(p) for p in candidates if p.is_file()),None)

def clean(text):
    text = re.sub(r'(https://)[^\s/@]+:[^\s/@]+@', r'\1[redacted]@', text)
    return re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b', '[redacted]', text)

def run(argv, cwd=None, timeout=40, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never', GIT_CONFIG_NOSYSTEM='1')
    env.pop('GIT_TRACE', None); env.pop('GIT_CURL_VERBOSE', None)
    for key in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_CONFIG_PARAMETERS','GIT_CONFIG_COUNT'):
        env.pop(key,None)
    # Finder-launched applications may omit Homebrew/GitHub CLI from PATH.
    env['PATH']=os.pathsep.join([str(Path(executable(n)).parent) for n in ('git','gh') if executable(n)]+[env.get('PATH','')])
    try:
        p = subprocess.run([str(v) for v in argv], cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env, creationflags=0x08000000 if os.name=='nt' else 0)
    except subprocess.TimeoutExpired: raise Failure('Operation timed out. Inspect the device/repository before retrying; an upload may be incomplete.')
    except OSError as e: raise Failure('Required tool could not start: '+str(e))
    out, err = clean(p.stdout.decode('utf-8','replace')), clean(p.stderr.decode('utf-8','replace'))
    if check and p.returncode: raise Failure(f'Tool exited {p.returncode}: {(err or out)[-6000:]}')
    return p.returncode, out, err

def git(root, *args, check=True):
    # Disable repository-provided hooks and external diff/textconv programs.
    return run([executable('git') or 'git','-c','core.hooksPath='+os.devnull,'-c','diff.external=','-c','credential.interactive=false', '-C',str(root), *args], timeout=120, check=check)

def repo(a):
    if not a.get('_root'): raise Failure('Choose the robot repository on the GitHub page first.')
    root=Path(a['_root']).resolve()
    if not root.is_dir(): raise Failure('Selected repository folder is unavailable.')
    if git(root,'rev-parse','--show-toplevel',check=False)[0]: raise Failure('This folder is not a Git repository. Clone into an empty folder or choose an existing checkout.')
    top=Path(git(root,'rev-parse','--show-toplevel')[1].strip()).resolve()
    if top!=root: raise Failure('Select the top-level robot repository folder.')
    return root

def scoped(root, name, suffix=None):
    if not isinstance(name,str) or not name or Path(name).is_absolute(): raise Failure('A relative repository path is required.')
    p=(root/name).resolve()
    if not p.is_relative_to(root) or any(part.startswith('.') for part in Path(name).parts): raise Failure('Path is outside the allowed repository files.')
    if suffix and p.suffix.lower() not in suffix: raise Failure('Unsupported file format.')
    return p

def data_dir(a):
    p=Path(a['_data']); p.mkdir(parents=True,exist_ok=True); return p

def confirmed(a):
    if a.get('confirmed') is not True: raise Failure('Review and confirm this operation first.')

def atomic_write(p, content):
    fd, tmp=tempfile.mkstemp(prefix='.cc-',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(content)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def source(root, name='src/main.py'):
    p=scoped(root,name,('.py',)); raw=p.read_bytes()
    if len(raw)>2_000_000: raise Failure('Python file exceeds the 2 MB editor limit.')
    try: text=raw.decode('utf-8'); tree=ast.parse(text)
    except (UnicodeError,SyntaxError) as e: raise Failure('Python diagnostics: '+str(e))
    return p,raw,text,tree

def assignments(tree):
    return {n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}

def literal(n):
    try: return ast.literal_eval(n.value)
    except (ValueError,TypeError): return None

def mapping_of(tree):
    targets={'intake_control':('intake','outtake'),'pulley_control':('cascade_up','cascade_down'),'claw_control':('angle_up','angle_down','claw_in','claw_out'),'coffin_calibration_control':('lower_reference','upper_reference')}
    result={}
    for fn in tree.body:
        if isinstance(fn,ast.FunctionDef) and fn.name in targets:
            attrs=sorted([n for n in ast.walk(fn) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='controller_1' and n.attr.startswith('button')], key=lambda n:(n.lineno,n.col_offset))
            # Calibration also checks the lift buttons; only A/Y assignments are mapping targets.
            if fn.name=='coffin_calibration_control': attrs=attrs[:2]
            if len(attrs)!=len(targets[fn.name]): raise Failure(f'Unsupported controller structure in {fn.name}; use the code editor to review it.')
            result.update(zip(targets[fn.name],[n.attr[6:] for n in attrs]))
    if set(result)!=set(DEFAULT_MAPPING): raise Failure('Robot control functions do not match the supported 94132B adapter.')
    return result

def validate_config(values,mapping):
    for key,value in values.items():
        if key in LIMITS:
            lo,hi=LIMITS[key]
            if type(value) not in (int,float) or not lo<=value<=hi: raise Failure(f'{key} must be between {lo} and {hi}.')
            if key not in ('DRIVE_SCALE','TURN_SCALE') and type(value)!=int: raise Failure(key+' must be a whole number.')
        elif key in FLAGS or key=='CLAW_HOLD':
            if type(value)!=bool: raise Failure(key+' must be enabled or disabled.')
        elif key=='REVERSE_DRIVE_BUTTON':
            if value not in BUTTONS: raise Failure('Unknown reverse-drive button.')
        else: raise Failure('Unsupported setting: '+key)
    if set(mapping)!=set(DEFAULT_MAPPING) or any(v not in BUTTONS for v in mapping.values()): raise Failure('Every action must use a real V5 controller button.')
    if len(set(mapping.values()))!=len(mapping): raise Failure('Two actions are assigned to the same button.')
    if values.get('REVERSE_DRIVE_ENABLED') and values.get('REVERSE_DRIVE_BUTTON') in mapping.values(): raise Failure('Reverse driving conflicts with another button assignment.')
    if values.get('PULLEY_LEFT_REVERSED')!=values.get('PULLEY_RIGHT_REVERSED'): raise Failure('Facing pulley motors must retain matching reversal flags because their spin commands are opposite.')

def hardware(tree):
    ports={}
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id in ('Motor','Inertial'):
            if n.value.args and isinstance(n.value.args[0],ast.Attribute):
                match=re.fullmatch(r'PORT(\d+)',n.value.args[0].attr)
                if match: ports[n.targets[0].id]=int(match[1])
    if any(not 1<=v<=21 for v in ports.values()) or len(set(ports.values()))!=len(ports): raise Failure('Invalid or duplicate motor/sensor ports.')
    if ports.get('imu')!=15 or any(ports.get(k)!=v for k,v in MOTORS.items()): raise Failure('Motor ports differ from the required 94132B hardware map; review code and wiring.')
    if 1 in ports.values(): raise Failure('Port 1 is reserved for the radio.')
    return ports

def config_read(a):
    _,raw,text,tree=source(repo(a),a.get('path','src/main.py'))
    nodes=assignments(tree)
    values={k:literal(nodes[k]) for k in (*LIMITS,*FLAGS,'REVERSE_DRIVE_BUTTON') if k in nodes}
    values.setdefault('REVERSE_DRIVE_ENABLED',False); values.setdefault('REVERSE_DRIVE_BUTTON','Left')
    values.setdefault('DRIVE_FORWARD_REVERSED',False); values.setdefault('TURN_REVERSED',False)
    values['CLAW_HOLD']='claw_rotate.set_stopping(HOLD)' in text and 'claw_rotate.stop(HOLD)' in text
    mapping=mapping_of(tree); ports=hardware(tree); validate_config(values,mapping)
    return dict(values=values,mapping=mapping,ports=ports,hash=digest(raw),travelLimits='Not implemented by this adapter; display references do not limit travel.',gravityCompensation='Not implemented; HOLD is available as a reviewed change.',reverseImplemented='REVERSE_DRIVE_ENABLED' in nodes)

def node_span(text,node):
    lines=text.splitlines(keepends=True)
    # AST columns are UTF-8 byte offsets.
    start=sum(len(x.encode()) for x in lines[:node.lineno-1])+node.col_offset
    end=sum(len(x.encode()) for x in lines[:node.end_lineno-1])+node.end_col_offset
    return start,end

def patch_config(a):
    root=repo(a); p,raw,text,tree=source(root,a.get('path','src/main.py'))
    if a.get('hash')!=digest(raw): raise Failure('Robot file changed since it was loaded. Reload before applying changes.')
    old=config_read(a); values=a['values']; mapping=a['mapping']
    if set(values)!=set(old['values']): raise Failure('Configuration schema changed. Reload configuration.')
    validate_config(values,mapping); hardware(tree)
    nodes=assignments(tree); edits=[]
    for k,v in values.items():
        if k in nodes and v!=literal(nodes[k]):
            start,end=node_span(text,nodes[k].value); edits.append((start,end,repr(v).encode()))
    changed_buttons={old['mapping'][k]:mapping[k] for k in mapping}
    for n in ast.walk(tree):
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='controller_1' and n.attr.startswith('button') and n.attr[6:] in changed_buttons:
            start,end=node_span(text,n); edits.append((start,end,('controller_1.button'+changed_buttons[n.attr[6:]]).encode()))
    new=raw
    for start,end,replacement in sorted(edits,reverse=True): new=new[:start]+replacement+new[end:]
    updated=new.decode(); newline='\r\n' if '\r\n' in text else '\n'
    # Guarded, small adapter migration. Existing Brain UI bytes are left intact.
    reverse_keys=('REVERSE_DRIVE_ENABLED','REVERSE_DRIVE_BUTTON','DRIVE_FORWARD_REVERSED','TURN_REVERSED')
    if 'REVERSE_DRIVE_ENABLED' not in nodes and any(values[k]!=old['values'][k] for k in reverse_keys):
        anchor='    left = forward * DRIVE_SCALE + turn * TURN_SCALE'
        if updated.count(anchor)!=1: raise Failure('Drive function changed; cannot safely add reverse control.')
        constants=newline.join(f'{k} = {repr(values[k])}' for k in ('REVERSE_DRIVE_ENABLED','REVERSE_DRIVE_BUTTON','DRIVE_FORWARD_REVERSED','TURN_REVERSED'))
        updated=constants+newline+newline+updated
        block=newline.join(('    if DRIVE_FORWARD_REVERSED:', '        forward = -forward', '    if REVERSE_DRIVE_ENABLED and getattr(controller_1, "button" + REVERSE_DRIVE_BUTTON).pressing():','        forward = -forward','    if TURN_REVERSED:', '        turn = -turn', ''))+newline
        updated=updated.replace(anchor,block+anchor)
    if values['CLAW_HOLD']!=old['values']['CLAW_HOLD']:
        if values['CLAW_HOLD']:
            before='def two_button_motor(motor, positive, negative, speed):'
            after='def two_button_motor(motor, positive, negative, speed, stop_mode=BRAKE):'
            if updated.count(before)==1:
                updated=updated.replace(before,after)
                start=updated.index(after); end=updated.index('\ndef ',start+len(after))
                section=updated[start:end]
                if section.count('motor.stop(BRAKE)')!=1: raise Failure('Unrecognized claw stopping logic.')
                updated=updated[:start]+section.replace('motor.stop(BRAKE)','motor.stop(stop_mode)')+updated[end:]
            elif updated.count(after)!=1: raise Failure('Claw helper changed; HOLD requires a manual code review.')
            if '        CLAW_ROTATE_SPEED, BRAKE'+newline in updated:
                updated=updated.replace('        CLAW_ROTATE_SPEED, BRAKE'+newline,'        CLAW_ROTATE_SPEED, HOLD'+newline)
            elif '        CLAW_ROTATE_SPEED'+newline in updated:
                updated=updated.replace('        CLAW_ROTATE_SPEED'+newline,'        CLAW_ROTATE_SPEED, HOLD'+newline)
            else: raise Failure('Claw call changed; review HOLD manually.')
            updated=updated.replace('claw_rotate.stop(BRAKE)','claw_rotate.stop(HOLD)').replace('claw_rotate.set_stopping(BRAKE)','claw_rotate.set_stopping(HOLD)')
        else:
            updated=updated.replace('        CLAW_ROTATE_SPEED, HOLD'+newline,'        CLAW_ROTATE_SPEED, BRAKE'+newline).replace('claw_rotate.stop(HOLD)','claw_rotate.stop(BRAKE)').replace('claw_rotate.set_stopping(HOLD)','claw_rotate.set_stopping(BRAKE)')
    ast.parse(updated); hardware(ast.parse(updated))
    diff=''.join(difflib.unified_diff(text.splitlines(True),updated.splitlines(True),fromfile=a.get('path','src/main.py'),tofile=a.get('path','src/main.py')))
    if a.get('apply'):
        confirmed(a)
        backup=data_dir(a)/'backups'/str(uuid.uuid4()); backup.parent.mkdir(exist_ok=True); backup.write_bytes(raw)
        if p.read_bytes()!=raw: raise Failure('File changed during review. Reload.')
        atomic_write(p,updated.encode()); return dict(saved=True,backup=str(backup),hash=digest(updated.encode()))
    return dict(diff=diff,hash=digest(raw))

def git_status(a):
    root=repo(a)
    remote=git(root,'remote','get-url','origin',check=False)[1].strip()
    return dict(repo=str(root),branch=git(root,'branch','--show-current')[1].strip(),commit=git(root,'log','-1','--format=%h %s',check=False)[1].strip(),changes=git(root,'status','--porcelain=v1')[1],remote=clean(remote),diff=git(root,'diff','--no-ext-diff','--no-textconv','HEAD','--')[1])

def auth_status(a):
    exe=executable('gh')
    authenticated=bool(exe) and run([exe,'auth','status','--hostname','github.com'],check=False)[0]==0
    log=data_dir(a)/'auth.log'; output=log.read_text(errors='replace') if log.exists() else ''
    codes=re.findall(r'\b[A-Z0-9]{4}-[A-Z0-9]{4}\b',output)
    return dict(available=bool(exe),authenticated=authenticated,deviceCode=codes[-1] if codes and not authenticated else None,url='https://github.com/login/device')

def auth_start(a):
    exe=executable('gh')
    if not exe: raise Failure('Install GitHub CLI (gh) or configure Git Credential Manager. Passwords and tokens are never entered into Control Center.')
    with (data_dir(a)/'auth.log').open('w') as log:
        subprocess.Popen([exe,'auth','login','--hostname','github.com','--git-protocol','https','--web'],stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=0x08000000 if os.name=='nt' else 0)
    return dict(started=True)

def git_action(a):
    root=repo(a); op=a['operation']
    if op=='pull' and git(root,'status','--porcelain')[1].strip(): raise Failure('Local changes block pull. Review, commit, stash, or cancel before pulling.')
    if op in ('pull','push'):
        remote=git(root,'remote','get-url','origin')[1].strip()
        if not re.fullmatch(r'(?:https://github\.com/|git@github\.com:)[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',remote): raise Failure('Synchronization requires an existing GitHub origin without embedded credentials.')
    if op=='pull':
        if git(root,'status','--porcelain')[1].strip(): raise Failure('Local changes block pull. Review, commit, stash, or cancel before pulling.')
        result=git(root,'pull','--ff-only','origin')
    elif op=='stash':
        confirmed(a); result=git(root,'stash','push','--include-untracked','-m','Control Center user-requested stash')
    elif op=='stash_list': return dict(output=git(root,'stash','list')[1])
    elif op=='stash_apply':
        confirmed(a); result=git(root,'stash','apply','stash@{0}')
    elif op=='commit':
        confirmed(a); files=a.get('files',[])
        if not files: raise Failure('Select the changed files to commit.')
        if git(root,'diff','--name-only','--cached')[1].strip(): raise Failure('Files are already staged. Review the existing Git index outside Control Center before committing.')
        for f in files:
            p=scoped(root,f)
            if p.suffix not in ('.py','.json','.md','.bmp') or any(w in p.name.lower() for w in ('secret','token','credential')): raise Failure('File requires manual security review before committing: '+f)
            if p.exists() and p.suffix!='.bmp':
                body=p.read_text(errors='replace')
                if re.search(r'(gh[pousr]_[A-Za-z0-9_]{10,}|github_pat_|-----BEGIN .*PRIVATE KEY|(?i:password|api_key|access_token)\s*=\s*[\'\"][^\'\"]+)',body): raise Failure('Possible secret detected: '+f)
        msg=a.get('message','').strip()
        if not msg or len(msg)>500: raise Failure('Enter a commit message under 500 characters.')
        git(root,'add','--',*files)
        result=git(root,'-c','commit.gpgsign=false','commit','-m',msg,'--',*files)
    elif op=='push':
        confirmed(a); result=git(root,'push','origin','HEAD')
    else: raise Failure('Unsupported Git operation.')
    return dict(output=result[1]+result[2],status=git_status(a))

def clone(a):
    confirmed(a)
    url=a.get('url','')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?',url): raise Failure('Enter a GitHub HTTPS repository URL without credentials.')
    if not a.get('_root'): raise Failure('Choose an empty destination folder first.')
    dest=Path(a['_root']).resolve()
    if not dest.is_dir() or any(dest.iterdir()): raise Failure('Clone destination must be an empty folder.')
    run([executable('git') or 'git','-c','core.hooksPath='+os.devnull,'clone','--',url,str(dest)],timeout=180)
    return git_status(a)

def files(a):
    root=repo(a)
    names=git(root,'ls-files','--cached','--others','--exclude-standard','-z')[1].split('\0')
    return sorted(set(n for n in names if n and n.endswith('.py') and not any(p.startswith('.') for p in Path(n).parts)))

def read_file(a):
    p=scoped(repo(a),a['path'],('.py',)); raw=p.read_bytes()
    if len(raw)>2_000_000: raise Failure('Editor limit is 2 MB.')
    return dict(text=raw.decode('utf-8'),hash=digest(raw))

def diagnose(a):
    try: ast.parse(a['text']); return []
    except SyntaxError as e: return [dict(line=e.lineno or 1,column=e.offset or 1,message=e.msg)]

def save_file(a):
    confirmed(a); p=scoped(repo(a),a['path'],('.py',)); old=p.read_bytes()
    if digest(old)!=a['hash']: raise Failure('File changed on disk. Reload to avoid overwriting someone else’s changes.')
    errors=diagnose(a)
    if errors: raise Failure('Fix Python syntax before saving: '+errors[0]['message'])
    backup=data_dir(a)/'backups'/str(uuid.uuid4()); backup.parent.mkdir(exist_ok=True); backup.write_bytes(old)
    atomic_write(p,a['text'].encode()); return dict(hash=digest(a['text'].encode()),backup=str(backup))

def tool(a):
    if a.get('_tool'): p=Path(a['_tool'])
    else:
        homes=[]; home=Path.home()
        if sys.platform=='darwin': homes=[home/'Library/Application Support/Code/User/globalStorage/vexrobotics.vexcode']
        elif os.name=='nt': homes=[Path(os.environ.get('APPDATA',''))/'Code/User/globalStorage/vexrobotics.vexcode']
        else: homes=[home/'.config/Code/User/globalStorage/vexrobotics.vexcode']
        platform='osx' if sys.platform=='darwin' else 'win32' if os.name=='nt' else 'linux-x64'
        name='vexcom.exe' if os.name=='nt' else 'vexcom'
        candidates=[p for h in homes for p in h.glob('tools/vexcom/**/'+platform+'/'+name)]
        if not candidates: raise Failure('VEX utility not found. Install the official VEX extension and initialize its tools, or choose your installed vexcom in Settings.')
        p=sorted(candidates,key=lambda p:p.stat().st_mtime,reverse=True)[0]
    if not p.is_file(): raise Failure('Selected vexcom utility is unavailable.')
    return p.resolve()

def tool_info(a):
    p=tool(a); code,out,err=run([p,'--version','--json'])
    return dict(path=str(p),version=json.loads(out).get('app',{}),physicalVerification='Pending — no hardware test has been performed by Control Center.')

def parse_devices(raw):
    try: payload=json.loads(raw)
    except ValueError: raise Failure('VEX discovery did not return valid JSON.')
    usb=payload.get('usb')
    if not isinstance(usb,(dict,list)): raise Failure('Unrecognized VEX discovery schema. Use official VEXcode until this utility version is supported.')
    found=[]
    def visit(node):
        if isinstance(node,dict):
            lower={k.lower():v for k,v in node.items()}
            platform=str(lower.get('platform','')).upper(); kind=str(lower.get('device',lower.get('type',''))).lower()
            communication=lower.get('communication',lower.get('communication_port'))
            if platform=='V5' and kind=='brain' and isinstance(communication,str) and communication:
                found.append(dict(id=str(lower.get('id',lower.get('serial',communication))),name=str(lower.get('name','V5 Brain')),port=communication,userPort=lower.get('user',lower.get('user_port')),platform='V5',type='brain'))
            else:
                for v in node.values(): visit(v)
        elif isinstance(node,list):
            for item in node: visit(item)
    visit(usb)
    return dict(devices=found,raw=payload,unrecognized=bool(usb) and not found)

def devices(a):
    p=tool(a); _,out,_=run([p,'--usb','--json'],timeout=15)
    result=parse_devices(out); result['tool']=str(p); return result

def current_device(a,identity):
    found=[d for d in devices(a)['devices'] if d['id']==identity]
    if len(found)!=1: raise Failure('Selected V5 Brain is disconnected or ambiguous. Scan and confirm again.')
    return found[0]

def prepare(a):
    root=repo(a); path=a.get('path','src/main.py'); _,raw,_,tree=source(root,path)
    config_read(dict(a,path=path)); hardware(tree)
    slot=a.get('slot')
    if type(slot)!=int or not 1<=slot<=8: raise Failure('Choose a V5 Brain slot from 1 through 8.')
    d=current_device(a,a.get('device'))
    p=tool(a); _,helptext,_=run([p,'--help'])
    if not all(x in helptext for x in ('--write','--slot','--load')): raise Failure('This vexcom version does not expose the verified command contract.')
    token=str(uuid.uuid4()); directory=data_dir(a)/'deployments'/token; directory.mkdir(parents=True)
    (directory/'main.py').write_bytes(raw)
    ticket=dict(token=token,repo=str(root),path=path,hash=digest(raw),slot=slot,device=d,tool=str(p),toolHash=digest(p.read_bytes()),created=time.time())
    (directory/'ticket.json').write_text(json.dumps(ticket))
    return dict(**ticket,warning='This overwrites the selected slot. The program will NOT be run. Brain must already have a compatible V5 Python VM; use official VEXcode to install/update it. Physical verification is pending.')

def ticket_path(a):
    try: token=str(uuid.UUID(a['token']))
    except (ValueError,KeyError): raise Failure('Invalid deployment review token.')
    return data_dir(a)/'deployments'/token

def flash(a):
    confirmed(a); directory=ticket_path(a); ticket=json.loads((directory/'ticket.json').read_text())
    if time.time()-ticket['created']>300: raise Failure('Deployment review expired. Prepare again.')
    if (directory/'attempted').exists(): raise Failure('This deployment was already attempted. Prepare again before retrying.')
    root=repo(a)
    if str(root)!=ticket['repo']: raise Failure('Repository changed after review.')
    _,raw,_,_=source(root,ticket['path'])
    if digest(raw)!=ticket['hash'] or digest((directory/'main.py').read_bytes())!=ticket['hash']: raise Failure('Program changed after review. Prepare again.')
    p=tool(a)
    if str(p)!=ticket['tool'] or digest(p.read_bytes())!=ticket['toolHash']: raise Failure('VEX utility changed after review.')
    d=current_device(a,ticket['device']['id'])
    if d!=ticket['device']: raise Failure('Device identity or ports changed. Prepare again.')
    (directory/'attempted').write_text(str(time.time()))
    # No --run or --load is passed here. The source .py is sent directly by vexcom.
    code,out,err=run([p,'--slot',str(ticket['slot']),'--write',directory/'main.py',d['port']],timeout=120)
    listing_code,listing,listing_error=run([p,'--programs',d['port']],check=False)
    verified=listing_code==0 and re.search(r'\bslot\s+'+str(ticket['slot'])+r'\s*:',listing,re.I) is not None
    receipt=dict(uploaded=True,slotVerified=verified,slot=ticket['slot'],device=d,hash=ticket['hash'],toolExitCode=code,output=out+err,programs=listing+listing_error,verification='Slot listing confirms presence, not a byte-for-byte readback.' if verified else 'Utility upload completed; slot listing could not be verified. Run remains disabled.')
    (directory/'receipt.json').write_text(json.dumps(receipt)); return receipt

def run_program(a):
    confirmed(a); directory=ticket_path(a); ticket=json.loads((directory/'ticket.json').read_text()); receipt=json.loads((directory/'receipt.json').read_text())
    if not receipt['uploaded'] or not receipt['slotVerified']: raise Failure('A verified upload is required before running.')
    if time.time()-ticket['created']>600: raise Failure('Run approval expired. Inspect the Brain before running manually.')
    d=current_device(a,ticket['device']['id'])
    if d!=ticket['device']: raise Failure('Device changed since upload.')
    p=tool(a)
    if digest(p.read_bytes())!=ticket['toolHash']: raise Failure('VEX utility changed since upload.')
    _,out,err=run([p,'--slot',str(ticket['slot']),'--load',d['port']])
    return dict(output=out+err)

def assets(a):
    root=repo(a); manifest=scoped(root,'assets/tile_manifest.json'); expected={}
    if manifest.exists():
        # Current repository uses 24 tiles for each of these four UI prefixes.
        content=json.loads(manifest.read_text())
        if isinstance(content,dict) and set(content)=={'logo','boot','auton','driver'}:
            for prefix in ('logo','boot','auton','driver'):
                names=[f'{prefix}{i:02}.bmp' for i in range(24)]
                if content[prefix]!=names: raise Failure('Tile manifest differs from the supported 94132B layout.')
                expected.update({name:(80,60) for name in names})
    found={p.name:p for p in (root/'assets/sdcard').glob('*.bmp')} if (root/'assets/sdcard').is_dir() else {}
    if not expected: raise Failure('Supported tile manifest not found. Review assets/SD_CARD_SETUP.md manually.')
    result=[]
    for name in sorted(set(expected)|set(found)):
        p=found.get(name); entry=dict(name=name,exists=bool(p),valid=False)
        if p:
            p=scoped(root,str(p.relative_to(root)),('.bmp',)); raw=p.read_bytes()
            if len(raw)>=54 and raw[:2]==b'BM':
                width,height=struct.unpack_from('<ii',raw,18); bpp=struct.unpack_from('<H',raw,28)[0]; compression=struct.unpack_from('<I',raw,30)[0]
                entry.update(width=width,height=height,bpp=bpp,compression=compression,valid=(width,abs(height))==expected.get(name,(80,60)) and bpp in (8,24) and compression==0 and len(raw)<=5878,preview='data:image/bmp;base64,'+base64.b64encode(raw).decode())
        result.append(entry)
    return result

def copy_assets(a):
    confirmed(a); root=repo(a); items=assets(a)
    if not all(x['valid'] for x in items): raise Failure('Resolve missing or invalid BMP assets before copying.')
    if not a.get('_sd'): raise Failure('Choose the accessible mounted SD folder first.')
    dest=Path(a['_sd']).resolve()
    if not dest.is_dir() or dest==Path(dest.anchor) or dest==Path.home() or dest.is_relative_to(root): raise Failure('Choose a separate SD card folder.')
    collisions=[x['name'] for x in items if (dest/x['name']).exists()]
    if collisions and not a.get('overwrite'): raise Failure('Destination contains matching filenames. Review and enable replacement before copying.')
    for item in items:
        target=dest/item['name']
        if target.is_symlink(): raise Failure('SD destination contains symbolic links.')
    for item in items:
        raw=scoped(root,'assets/sdcard/'+item['name'],('.bmp',)).read_bytes()
        atomic_write(dest/item['name'],raw)
        if (dest/item['name']).read_bytes()!=raw: raise Failure('SD copy verification failed.')
    return dict(copied=len(items),destination=str(dest))

HANDLERS={'config_read':config_read,'config_preview':patch_config,'git_status':git_status,'git_action':git_action,'auth_status':auth_status,'auth_start':auth_start,'clone':clone,'files':files,'read_file':read_file,'diagnose':diagnose,'save_file':save_file,'tool_info':tool_info,'devices':devices,'prepare':prepare,'flash':flash,'run_program':run_program,'assets':assets,'copy_assets':copy_assets}

def main():
    try:
        request=json.loads(sys.stdin.buffer.read(4_000_000))
        if request['action'] not in HANDLERS: raise Failure('Unknown local operation.')
        result=HANDLERS[request['action']](request.get('args',{})); response=dict(ok=True,result=result)
    except Exception as error: response=dict(ok=False,error=clean(str(error)))
    print(json.dumps(response,ensure_ascii=False))

if __name__=='__main__': main()
