export type Values = Record<string, number | string | boolean>;
export type Mapping = Record<string, string>;
export type ControlState = {values: Values; mapping: Mapping};
export type MappingPreset = {mapping: Mapping; reverse?: Values};

export const reverseDefaults: Values = {
  REVERSE_DRIVE_ENABLED: true, REVERSE_DRIVE_BUTTON: 'Left', REVERSE_DRIVE_MODE: 'TOGGLE',
};
export const reverseLabel = (values: Values) =>
  values.REVERSE_DRIVE_MODE === 'TOGGLE' ? 'Toggle Reverse Drive' : 'Hold to Reverse Drive';

export function assignments(state: ControlState): Mapping {
  const result = {...state.mapping};
  if (state.values.REVERSE_DRIVE_ENABLED) result.reverse_drive = String(state.values.REVERSE_DRIVE_BUTTON);
  return result;
}

export function conflicts(state: ControlState): string[] {
  const entries = Object.entries(assignments(state));
  return entries.filter(([key, button]) => entries.some(([other, value]) => other !== key && value === button)).map(([key]) => key);
}

export function makePreset(state: ControlState): MappingPreset {
  return {mapping: {...state.mapping}, reverse: Object.fromEntries(
    Object.keys(reverseDefaults).filter(key => key in state.values).map(key => [key, state.values[key]]))};
}

export function applyPreset<T extends ControlState>(state: T, preset: MappingPreset | Mapping): T {
  // Older locally saved presets contain mappings only. They retain the loaded
  // reverse settings rather than silently activating a new reverse behavior.
  if ('mapping' in preset && typeof preset.mapping === 'object') {
    const current = preset as MappingPreset;
    return {...state, mapping: {...current.mapping}, values: {...state.values, ...current.reverse}};
  }
  return {...state, mapping: {...preset as Mapping}};
}
