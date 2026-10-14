"""Synthetic service and process-contract tests. These are NOT hardware tests."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('service',Path(__file__).parents[1]/'service/main.py')
service=importlib.util.module_from_spec(spec); spec.loader.exec_module(service)

def fixture():
    declarations='\n'.join(f'{k} = {0.6 if k=="DRIVE_SCALE" else 0.35 if k=="TURN_SCALE" else 5 if k=="DEADZONE" else 35 if k=="CLAW_TORQUE_LIMIT" else 50}' for k in service.LIMITS)
    flags='\n'.join(f'{k} = False' for k in service.FLAGS if k not in ('REVERSE_DRIVE_ENABLED','DRIVE_FORWARD_REVERSED','TURN_REVERSED'))
    motors='\n'.join(f'{name} = Motor(Ports.PORT{port}, GEARS, {name.upper()}_REVERSED)' for name,port in service.MOTORS.items())
    return declarations+'\n'+flags+'\n'+motors+'''\nimu = Inertial(Ports.PORT15)
# Preserve this non-ASCII UI: café / 94132B / ✧
class RobotUI:
    ART = "original artwork remains unchanged"

def two_button_motor(motor, positive, negative, speed):
    if positive:
        motor.spin(FORWARD, speed, PERCENT)
    else:
        motor.stop(BRAKE)

def drive_control():
    forward = controller_1.axis3.position()
    turn = controller_1.axis1.position()
    left = forward * DRIVE_SCALE + turn * TURN_SCALE
    right = forward * DRIVE_SCALE - turn * TURN_SCALE

def intake_control():
    inward = controller_1.buttonR1.pressing()
    outward = controller_1.buttonR2.pressing()

def pulley_control():
    direction_a = controller_1.buttonL1.pressing()
    direction_b = controller_1.buttonL2.pressing()

def claw_control():
    two_button_motor(
        claw_rotate,
        controller_1.buttonUp.pressing(),
        controller_1.buttonDown.pressing(),
        CLAW_ROTATE_SPEED
    )
    two_button_motor(
        claw_activate,
        controller_1.buttonX.pressing(),
        controller_1.buttonB.pressing(),
        CLAW_ACTIVATE_SPEED
    )

def coffin_calibration_control():
    a = controller_1.buttonA.pressing()
    y = controller_1.buttonY.pressing()
    stationary = not controller_1.buttonL1.pressing() and not controller_1.buttonL2.pressing()

def stop_all():
    claw_rotate.stop(BRAKE)

claw_rotate.set_stopping(BRAKE)
claw_activate.set_stopping(BRAKE)
'''

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=(Path(self.tmp.name)/'robot').resolve(); self.root.mkdir(); (self.root/'src').mkdir()
        self.file=self.root/'src/main.py'; self.file.write_text(fixture(),encoding='utf-8')
        self.data=Path(self.tmp.name)/'appdata'; self.data.mkdir()
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        for k,v in [('user.name','Test'),('user.email','test@example.invalid')]: subprocess.run(['git','-C',str(self.root),'config',k,v],check=True)
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','Fixture'],check=True)
        self.a={'_root':str(self.root),'_data':str(self.data)}
    def config(self): return {**self.a,**service.config_read(self.a)}
    def test_config_preview_is_read_only(self):
        before=self.file.read_bytes(); a=self.config(); a['values']['INTAKE_SPEED']=62
        preview=service.patch_config(a)
        self.assertIn('+INTAKE_SPEED = 62',preview['diff']); self.assertEqual(before,self.file.read_bytes())
    def test_confirmation_and_hash_protect_file(self):
        a=self.config(); a.update(apply=True)
        with self.assertRaises(service.Failure): service.patch_config(a)
        a['confirmed']=True; self.file.write_text(self.file.read_text(encoding='utf-8')+'\n# changed\n',encoding='utf-8')
        with self.assertRaises(service.Failure): service.patch_config(a)
    def test_patch_preserves_ui_and_backs_up(self):
        before=self.file.read_text(encoding='utf-8'); a=self.config(); a['values']['CLAW_HOLD']=True; a.update(apply=True,confirmed=True)
        result=service.patch_config(a); after=self.file.read_text(encoding='utf-8')
        self.assertEqual(Path(result['backup']).read_text(encoding='utf-8'),before)
        self.assertEqual(before[before.index('class RobotUI:'):before.index('def two_button_motor')],after[after.index('class RobotUI:'):after.index('def two_button_motor')])
        self.assertIn('CLAW_ROTATE_SPEED, HOLD',after); self.assertIn('claw_activate.set_stopping(BRAKE)',after)
        self.assertTrue(service.config_read(self.a)['values']['CLAW_HOLD'])
    def test_button_swap_updates_stationary_guard_simultaneously(self):
        a=self.config(); a['mapping']['cascade_up']='R1'; a['mapping']['intake']='L1'; a.update(apply=True,confirmed=True)
        service.patch_config(a); text=self.file.read_text(encoding='utf-8')
        self.assertIn('stationary = not controller_1.buttonR1',text)
        self.assertIn('inward = controller_1.buttonL1',text)
    def test_conflicts_and_motor_protection(self):
        a=self.config(); a['mapping']['intake']='L1'
        with self.assertRaises(service.Failure): service.patch_config(a)
        for key,val in [('INTAKE_SPEED',101),('PULLEY_LEFT_REVERSED',True),('CLAW_TORQUE_LIMIT',36)]:
            a=self.config(); a['values'][key]=val
            with self.assertRaises(service.Failure): service.patch_config(a)
    def test_reverse_does_not_change_turn(self):
        a=self.config(); a['values']['REVERSE_DRIVE_ENABLED']=True; a.update(apply=True,confirmed=True); service.patch_config(a)
        tree=ast.parse(self.file.read_text(encoding='utf-8')); drive=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='drive_control')
        reverse=next(n for n in ast.walk(drive) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp))
        self.assertEqual([n.targets[0].id for n in reverse.body if isinstance(n,ast.Assign)],['forward'])
    def test_escape_and_symlink_rejected(self):
        for name in ('../outside.py','/tmp/outside.py','.git/config'):
            with self.assertRaises(service.Failure): service.scoped(self.root,name)
        (self.root/'src/escape.py').symlink_to(self.data/'outside.py')
        with self.assertRaises(service.Failure): service.scoped(self.root,'src/escape.py')
    def test_duplicate_ports_rejected(self):
        self.file.write_text(self.file.read_text(encoding='utf-8').replace('Ports.PORT14','Ports.PORT13'),encoding='utf-8')
        with self.assertRaises(service.Failure): service.config_read(self.a)
    def test_save_file_does_not_execute(self):
        text='raise RuntimeError("must not execute")\n'
        result=service.save_file({**self.a,'path':'src/main.py','text':text,'hash':service.digest(self.file.read_bytes()),'confirmed':True})
        self.assertEqual(self.file.read_text(encoding='utf-8'),text); self.assertTrue(result['backup'])
    def test_dirty_pull_never_discards(self):
        self.file.write_text(self.file.read_text(encoding='utf-8')+'\n# local\n',encoding='utf-8')
        with self.assertRaisesRegex(service.Failure,'Local changes'): service.git_action({**self.a,'operation':'pull'})
        self.assertIn('# local',self.file.read_text(encoding='utf-8'))
    def test_commit_only_selected_files(self):
        self.file.write_text(self.file.read_text(encoding='utf-8')+'\n# local\n',encoding='utf-8'); (self.root/'notes.md').write_text('leave uncommitted')
        service.git_action({**self.a,'operation':'commit','files':['src/main.py'],'message':'Tune fixture','confirmed':True})
        self.assertIn('notes.md',service.git_status(self.a)['changes']); self.assertNotIn('src/main.py',service.git_status(self.a)['changes'])
    def test_device_parser_refuses_other_platform_and_schema(self):
        self.assertEqual(service.parse_devices('{"usb":{}}')['devices'],[])
        self.assertTrue(service.parse_devices('{"usb":{"unexpected":"connected"}}')['unrecognized'])
        payload={'usb':{'devices':[{'platform':'V5','device':'brain','communication':'COM7','user':'COM8','id':'123'},{'platform':'IQ2','device':'brain','communication':'COM9'}]}}
        result=service.parse_devices(json.dumps(payload))
        self.assertEqual(len(result['devices']),1); self.assertEqual(result['devices'][0]['port'],'COM7')
    def test_flash_contract_never_runs_and_requires_slot_confirmation(self):
        fake_tool=self.data/'vexcom'; fake_tool.write_bytes(b'synthetic-test-binary')
        d={'id':'synthetic-device','name':'Synthetic Brain','port':'COM7','userPort':'COM8','platform':'V5','type':'brain'}
        a={**self.a,'_tool':str(fake_tool),'device':d['id'],'slot':3}
        calls=[]
        def fake_run(argv,**kw):
            calls.append([str(v) for v in argv]); return (0,'--write --slot --load' if '--help' in argv else 'slot 3: name main' if '--programs' in argv else '', '')
        with patch.object(service,'repo',return_value=self.root),patch.object(service,'current_device',return_value=d),patch.object(service,'run',side_effect=fake_run):
            ticket=service.prepare(a); r=service.flash({**a,'token':ticket['token'],'confirmed':True})
        writes=[args for args in calls if '--write' in args]
        self.assertEqual(len(writes),1); self.assertNotIn('--run',writes[0]); self.assertNotIn('--load',writes[0]); self.assertTrue(r['slotVerified'])
    def test_failed_upload_never_creates_success_receipt(self):
        fake_tool=self.data/'vexcom'; fake_tool.write_bytes(b'synthetic-test-binary')
        d={'id':'synthetic-device','name':'Synthetic Brain','port':'COM7'}; a={**self.a,'_tool':str(fake_tool),'device':d['id'],'slot':1}
        with patch.object(service,'repo',return_value=self.root),patch.object(service,'current_device',return_value=d),patch.object(service,'run',return_value=(0,'--write --slot --load','')): ticket=service.prepare(a)
        with patch.object(service,'repo',return_value=self.root),patch.object(service,'current_device',return_value=d),patch.object(service,'run',side_effect=service.Failure('USB disconnected')):
            with self.assertRaises(service.Failure): service.flash({**a,'token':ticket['token'],'confirmed':True})
        self.assertFalse((self.data/'deployments'/ticket['token']/'receipt.json').exists())
    def test_secret_redaction(self):
        self.assertNotIn('ghp_abcdefghijk',service.clean('ghp_abcdefghijk'))
        self.assertNotIn('secret',service.clean('https://user:secret@github.com/foo/bar'))

if __name__=='__main__': unittest.main()
