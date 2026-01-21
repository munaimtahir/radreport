import { describe, it, expect } from 'vitest';
import { 
  normalizeTemplateSchema, 
  normalizeOptions, 
  getFieldKey 
} from '../normalizeTemplateSchema';

describe('normalizeTemplateSchema', () => {
  it('should return null for null input', () => {
    expect(normalizeTemplateSchema(null)).toBe(null);
  });

  it('should return null for undefined input', () => {
    expect(normalizeTemplateSchema(undefined)).toBe(null);
  });

  it('should normalize field with key to field_key', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { key: 'my_field', label: 'My Field' }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    expect(result?.sections[0].fields[0].field_key).toBe('my_field');
  });

  it('should prefer existing field_key over key', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { key: 'old_key', field_key: 'new_key', label: 'My Field' }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    expect(result?.sections[0].fields[0].field_key).toBe('new_key');
  });

  it('should normalize field_type to type', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { key: 'f1', field_type: 'text', label: 'My Field' }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    expect(result?.sections[0].fields[0].type).toBe('text');
  });

  it('should prefer existing type over field_type', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { key: 'f1', field_type: 'old_type', type: 'new_type', label: 'My Field' }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    expect(result?.sections[0].fields[0].type).toBe('new_type');
  });

  it('should convert string array options to {label, value} format', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { 
              key: 'f1', 
              label: 'My Field',
              options: ['Option A', 'Option B', 'Option C']
            }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    const options = result?.sections[0].fields[0].options;
    expect(options).toEqual([
      { label: 'Option A', value: 'Option A' },
      { label: 'Option B', value: 'Option B' },
      { label: 'Option C', value: 'Option C' }
    ]);
  });

  it('should preserve existing {label, value} options', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { 
              key: 'f1', 
              label: 'My Field',
              options: [
                { label: 'Label A', value: 'val_a' },
                { label: 'Label B', value: 'val_b' }
              ]
            }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    const options = result?.sections[0].fields[0].options;
    expect(options).toEqual([
      { label: 'Label A', value: 'val_a' },
      { label: 'Label B', value: 'val_b' }
    ]);
  });

  it('should handle show_if.field_key fallback to show_if.field', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { 
              key: 'f1', 
              label: 'My Field',
              rules: {
                show_if: {
                  field_key: 'other_field',
                  value: 'yes'
                }
              }
            }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    const rules = result?.sections[0].fields[0].rules;
    expect(rules?.show_if?.field).toBe('other_field');
  });

  it('should preserve existing show_if.field', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { 
              key: 'f1', 
              label: 'My Field',
              rules: {
                show_if: {
                  field: 'existing_field',
                  value: 'yes'
                }
              }
            }
          ]
        }
      ]
    };

    const result = normalizeTemplateSchema(input);
    const rules = result?.sections[0].fields[0].rules;
    expect(rules?.show_if?.field).toBe('existing_field');
  });

  it('should not mutate input objects', () => {
    const input = {
      sections: [
        {
          section_key: 's1',
          fields: [
            { key: 'my_field', label: 'My Field' }
          ]
        }
      ]
    };

    const originalField = input.sections[0].fields[0];
    normalizeTemplateSchema(input);
    
    // Original should not have field_key added
    expect(originalField).not.toHaveProperty('field_key');
  });

  it('should handle empty sections array', () => {
    const input = {
      sections: []
    };

    const result = normalizeTemplateSchema(input);
    expect(result?.sections).toEqual([]);
  });

  it('should handle missing sections property', () => {
    const input = {};

    const result = normalizeTemplateSchema(input);
    expect(result?.sections).toEqual([]);
  });
});

describe('normalizeOptions', () => {
  it('should return empty array for non-array input', () => {
    expect(normalizeOptions(undefined)).toEqual([]);
    expect(normalizeOptions(null as any)).toEqual([]);
    expect(normalizeOptions('string' as any)).toEqual([]);
  });

  it('should convert strings to {label, value} objects', () => {
    const result = normalizeOptions(['A', 'B', 'C']);
    expect(result).toEqual([
      { label: 'A', value: 'A' },
      { label: 'B', value: 'B' },
      { label: 'C', value: 'C' }
    ]);
  });

  it('should preserve existing {label, value} objects', () => {
    const input = [
      { label: 'Label A', value: 'val_a' },
      { label: 'Label B', value: 'val_b' }
    ];
    const result = normalizeOptions(input);
    expect(result).toEqual(input);
  });

  it('should filter out null/undefined values', () => {
    const result = normalizeOptions(['A', null, 'B', undefined, 'C']);
    expect(result).toEqual([
      { label: 'A', value: 'A' },
      { label: 'B', value: 'B' },
      { label: 'C', value: 'C' }
    ]);
  });

  it('should handle objects with value but no label', () => {
    const result = normalizeOptions([{ value: 'test' }]);
    expect(result).toEqual([{ label: 'test', value: 'test' }]);
  });
});

describe('getFieldKey', () => {
  it('should return field_key if present', () => {
    expect(getFieldKey({ field_key: 'my_key' })).toBe('my_key');
  });

  it('should fallback to key if field_key not present', () => {
    expect(getFieldKey({ key: 'my_key' })).toBe('my_key');
  });

  it('should prefer field_key over key', () => {
    expect(getFieldKey({ field_key: 'new_key', key: 'old_key' })).toBe('new_key');
  });

  it('should return empty string if neither present', () => {
    expect(getFieldKey({})).toBe('');
  });
});
