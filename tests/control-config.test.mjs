import {test} from 'node:test';
import assert from 'node:assert/strict';
import {assignments, conflicts, makePreset, applyPreset, reverseDefaults, reverseLabel} from '../src/controlConfig.ts';

const state=()=>({values:{...reverseDefaults,CLAW_ROTATION_SPEED:25,CLAW_TORQUE_LIMIT:35},mapping:{intake:'R1',cascade_down:'L2'}});
test('Left is the default toggle assignment; duplicate reverse inputs are visible',()=>{
  const current=state(); assert.equal(assignments(current).reverse_drive,'Left');
  assert.equal(reverseLabel(current.values),'Toggle Reverse Drive');
  current.values.REVERSE_DRIVE_BUTTON='L2'; assert.deepEqual(conflicts(current),['cascade_down','reverse_drive']);
  current.values.REVERSE_DRIVE_ENABLED=false; assert.deepEqual(conflicts(current),[]);
});
test('mapping presets persist reverse mode/button/enabled without changing torque or speeds',()=>{
  const current=state(); current.values.REVERSE_DRIVE_MODE='HOLD'; current.values.REVERSE_DRIVE_BUTTON='Right';
  const saved=JSON.parse(JSON.stringify(makePreset(current)));
  const next=state(); next.values.CLAW_ROTATION_SPEED=30;
  const applied=applyPreset(next,saved);
  assert.equal(applied.values.REVERSE_DRIVE_MODE,'HOLD'); assert.equal(applied.values.REVERSE_DRIVE_BUTTON,'Right');
  assert.equal(applied.values.CLAW_ROTATION_SPEED,30); assert.equal(applied.values.CLAW_TORQUE_LIMIT,35);
  assert.equal(next.values.REVERSE_DRIVE_MODE,'TOGGLE');
});
test('old locally saved mapping presets retain loaded reverse settings',()=>{
  const current=state(); current.values.REVERSE_DRIVE_ENABLED=false;
  assert.equal(applyPreset(current,{intake:'R2',cascade_down:'L2'}).values.REVERSE_DRIVE_ENABLED,false);
});
