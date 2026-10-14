"""Windows detection fixtures, using the official VEX VID/PID/interface IDs.

These are synthetic records, not a claim of testing the user's Windows Brain.
"""
import json
import os
import unittest
from unittest.mock import patch

import test_service
service=test_service.service


def port(number,interface='00',identity='7&ABC&0',**extra):
    return dict(Name=f'VEX Robotics V5 ({number})',
                PNPDeviceID=f'USB\\VID_2888&PID_0501&MI_{interface}\\{identity}&00{interface}',
                Present=True,ConfigManagerErrorCode=0,**extra)


class WindowsDeviceTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Native Windows inventory requires Windows')
    def test_native_inventory_command_runs_on_windows(self):
        devices,inventory=service.windows_v5_ports()
        self.assertIsInstance(devices,list)
        self.assertIsInstance(inventory,(list,dict))

    def test_communication_and_user_interfaces_are_paired_without_guessing_com_order(self):
        records=[port('COM23','02'),port('COM24','00')]
        result=service.parse_windows_v5_ports(json.dumps(records))
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['port'],'COM24')
        self.assertEqual(result[0]['userPort'],'COM23')

    def test_single_object_and_missing_user_port_are_supported(self):
        result=service.parse_windows_v5_ports(json.dumps(port('COM7')))
        self.assertEqual(result[0]['port'],'COM7')
        self.assertIsNone(result[0]['userPort'])
        self.assertEqual(service.parse_windows_v5_ports(''),[])

    def test_user_only_wrong_hardware_disconnected_or_error_records_are_rejected(self):
        candidates=[port('COM4','02'),port('COM5'),port('COM6'),port('COM7'),port('COM8')]
        candidates[1]['Present']=False
        candidates[2]['ConfigManagerErrorCode']=10
        candidates[3]['PNPDeviceID']=candidates[3]['PNPDeviceID'].replace('PID_0501','PID_0503')
        candidates[4]['PNPDeviceID']=candidates[4]['PNPDeviceID'].replace('VID_2888','VID_1234')
        self.assertEqual(service.parse_windows_v5_ports(json.dumps(candidates)),[])

    def test_two_brains_keep_distinct_ids_and_ports(self):
        first=service.parse_windows_v5_ports(json.dumps([port('COM7'),port('COM8','00','8&XYZ&0')]))
        second=service.parse_windows_v5_ports(json.dumps([port('COM7'),port('COM8','00','8&XYZ&0')]))
        self.assertEqual(first,second)
        self.assertEqual(len({item['id'] for item in first}),2)

    def test_ambiguous_interfaces_and_invalid_json_fail(self):
        with self.assertRaises(service.Failure):
            service.parse_windows_v5_ports(json.dumps([port('COM7'),port('COM9')]))
        with self.assertRaises(service.Failure): service.parse_windows_v5_ports('not json')

    def test_family_field_in_vex_usb_json_is_supported(self):
        result=service.parse_devices(json.dumps({'usb':{'vex':[{
            'family':'V5','device':'brain','communication':'COM7','user':'COM8'}]}}))
        self.assertEqual(result['devices'][0]['port'],'COM7')

    def test_native_windows_discovery_recovers_from_unrecognized_usb_shape(self):
        # Never change the real interpreter's os.name/Path flavor.
        class WindowsOS:
            name='nt'
        native=service.parse_windows_v5_ports(json.dumps(port('COM7')))
        with patch.object(service,'os',WindowsOS),patch.object(service,'tool',return_value='vexcom.exe'),\
             patch.object(service,'run',return_value=(0,'{"usb":{"vex":[{"family":"V5"}]}}','')),\
             patch.object(service,'windows_v5_ports',return_value=(native,[port('COM7')])):
            result=service.devices({})
        self.assertFalse(result['unrecognized'])
        self.assertEqual(result['devices'][0]['port'],'COM7')
        self.assertIn('Windows',result['discoveryMethod'])

    def test_blocked_windows_query_preserves_diagnostics_and_never_invents_a_device(self):
        class WindowsOS:
            name='nt'
        with patch.object(service,'os',WindowsOS),patch.object(service,'tool',return_value='vexcom.exe'),\
             patch.object(service,'run',return_value=(0,'{"usb":{"unknown":true}}','')),\
             patch.object(service,'windows_v5_ports',side_effect=service.Failure('Access denied')):
            result=service.devices({})
        self.assertTrue(result['unrecognized'])
        self.assertEqual(result['devices'],[])
        self.assertIn('Access denied',result['windowsDiscoveryError'])

    def test_native_windows_discovery_survives_failed_utility_scan(self):
        class WindowsOS:
            name='nt'
        native=service.parse_windows_v5_ports(json.dumps(port('COM7')))
        with patch.object(service,'os',WindowsOS),patch.object(service,'tool',return_value='vexcom.exe'),\
             patch.object(service,'run',side_effect=service.Failure('USB scan failed')),\
             patch.object(service,'windows_v5_ports',return_value=(native,[port('COM7')])):
            result=service.devices({})
        self.assertFalse(result['unrecognized'])
        self.assertEqual(result['devices'][0]['port'],'COM7')
        self.assertEqual(result['discoveryError'],'USB scan failed')


if __name__=='__main__': unittest.main()
