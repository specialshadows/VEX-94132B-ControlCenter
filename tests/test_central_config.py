"""Round-trip the actual robot v2 layout. Never import/run the robot program."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import test_service
service = test_service.service


class CentralConfigTests(unittest.TestCase):
    def setUp(self):
        test_service.ServiceTests.setUp(self)
        self.file.write_bytes((Path(__file__).parent/'fixtures/central_robot.py').read_bytes())

    def config(self):
        return {**self.a, **service.config_read(self.a)}

    def test_reads_actual_defaults_and_nonliteral_hold_correctly(self):
        config=self.config()
        self.assertEqual(config['schemaVersion'],2)
        for key,value in {'REVERSE_DRIVE_BUTTON':'Left','REVERSE_DRIVE_MODE':'TOGGLE',
            'REVERSE_DRIVE_ENABLED':True,'CLAW_HOLD_ENABLED':True,'CLAW_HOLD_MODE':'HOLD',
            'CLAW_GRAVITY_COMPENSATION_ENABLED':False,'CLAW_ROTATION_SPEED':25,
            'CLAW_INOUT_SPEED':20,'CLAW_TORQUE_LIMIT':100}.items():
            self.assertEqual(config['values'][key],value)
        self.assertEqual(config['mapping']['cascade_down'],'L2')
        self.assertEqual(config['ports']['claw_rotate'],4)
        self.assertEqual(config['ports']['claw_activate'],3)
        self.assertEqual(service.patch_config(config)['diff'],'')

    def test_save_round_trip_preserves_all_runtime_functions_and_makes_backup(self):
        before=self.file.read_bytes(); config=self.config()
        config['values'].update(REVERSE_DRIVE_BUTTON='Right',REVERSE_DRIVE_MODE='HOLD',
                                REVERSE_DRIVE_ENABLED=False,CLAW_HOLD_ENABLED=False)
        config['mapping']['intake']='Left'
        preview=service.patch_config(config)
        self.assertIn("REVERSE_DRIVE_MODE = 'HOLD'",preview['diff'])
        self.assertEqual(self.file.read_bytes(),before)
        saved=service.patch_config(dict(config,apply=True,confirmed=True))
        self.assertEqual(Path(saved['backup']).read_bytes(),before)
        loaded=self.config()
        self.assertEqual(loaded['values'],config['values'])
        self.assertEqual(loaded['mapping'],config['mapping'])
        text=self.file.read_text(); self.assertIn("INTAKE_IN_BUTTON = 'LEFT'",text)
        for tree in (ast.parse(before),ast.parse(text)):
            protected=ast.dump(ast.Module(body=[node for node in tree.body
                if isinstance(node,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]))
            if tree is not None:
                if 'original' not in locals(): original=protected
                else: self.assertEqual(protected,original)

    def test_toggle_and_hold_both_save_and_remapping_does_not_rewire_button_table(self):
        for mode in ('HOLD','TOGGLE','HOLD','TOGGLE'):
            config=self.config(); config['values']['REVERSE_DRIVE_MODE']=mode
            service.patch_config(dict(config,apply=True,confirmed=True))
            self.assertEqual(self.config()['values']['REVERSE_DRIVE_MODE'],mode)
        config=self.config(); config['mapping']['cascade_down']='R2'; config['mapping']['outtake']='L2'
        before=service.assignments(ast.parse(self.file.read_text()))['CONTROLLER_BUTTONS']
        service.patch_config(dict(config,apply=True,confirmed=True))
        after=service.assignments(ast.parse(self.file.read_text()))['CONTROLLER_BUTTONS']
        self.assertEqual(ast.dump(before),ast.dump(after))
        self.assertEqual(self.config()['mapping']['cascade_down'],'R2')

    def test_conflicts_invalid_modes_and_unimplemented_compensation_are_blocked(self):
        for key,value in [('REVERSE_DRIVE_BUTTON','L2'),('REVERSE_DRIVE_MODE','LATCH'),
            ('CLAW_GRAVITY_COMPENSATION_ENABLED',True),('CLAW_HOLD_MODE','PID'),
            ('CASCADE_CONTROL_MODE','AUTOMATIC'),('CLAW_ROTATION_SPEED',101)]:
            with self.subTest(setting=key):
                config=self.config(); config['values'][key]=value
                with self.assertRaises(service.Failure): service.patch_config(config)
        config=self.config(); config['values'].update(REVERSE_DRIVE_ENABLED=False,REVERSE_DRIVE_BUTTON='L2')
        service.patch_config(config)

    def test_torque_increase_requires_explicit_warning_approval(self):
        self.file.write_text(self.file.read_text().replace('CLAW_TORQUE_LIMIT = 100','CLAW_TORQUE_LIMIT = 35'))
        config=self.config(); config['values']['CLAW_TORQUE_LIMIT']=40
        before=self.file.read_bytes()
        self.assertIn('heating',service.patch_config(config)['warnings'][0])
        with self.assertRaisesRegex(service.Failure,'approval'):
            service.patch_config(dict(config,apply=True,confirmed=True))
        self.assertEqual(self.file.read_bytes(),before)

    def test_deployment_stages_exact_saved_robot_program_and_changes_invalidate_review(self):
        config=self.config(); config['values']['REVERSE_DRIVE_MODE']='HOLD'
        service.patch_config(dict(config,apply=True,confirmed=True))
        fake_tool=self.data/'vexcom'; fake_tool.write_bytes(b'synthetic')
        device={'id':'synthetic','name':'Synthetic Brain','port':'COM7'}
        args={**self.a,'_tool':str(fake_tool),'device':'synthetic','slot':1}
        with patch.object(service,'repo',return_value=self.root),patch.object(service,'current_device',return_value=device),patch.object(service,'run',return_value=(0,'--write --slot --load','')):
            ticket=service.prepare(args)
        staged=self.data/'deployments'/ticket['token']/'main.py'
        self.assertEqual(staged.read_bytes(),self.file.read_bytes())
        self.assertEqual(ticket['hash'],service.digest(self.file.read_bytes()))
        config=self.config(); config['values']['REVERSE_DRIVE_MODE']='TOGGLE'
        service.patch_config(dict(config,apply=True,confirmed=True))
        with self.assertRaisesRegex(service.Failure,'changed'):
            service.flash(dict(args,token=ticket['token'],confirmed=True))


if __name__=='__main__': unittest.main()
