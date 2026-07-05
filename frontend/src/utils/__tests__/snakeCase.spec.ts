import { describe, it, expect } from 'vitest';
import { toSnakeCase, toSnakeCaseArray } from '../snakeCase';

describe('toSnakeCase', () => {
  it('converts camelCase keys to snake_case', () => {
    const result = toSnakeCase({ sourceSystem: 'image_2d', objectNumber: 'G123' });
    expect(result).toEqual({ source_system: 'image_2d', object_number: 'G123' });
  });

  it('handles empty object', () => {
    expect(toSnakeCase({})).toEqual({});
  });

  it('preserves already snake_case keys', () => {
    const result = toSnakeCase({ source_system: 'video', 'already_snake': true });
    expect(result.source_system).toBe('video');
    expect(result.already_snake).toBe(true);
  });

  it('handles single-letter prefixes', () => {
    const result = toSnakeCase({ aKey: 'value' });
    expect(result).toEqual({ a_key: 'value' });
  });

  it('preserves non-string values', () => {
    const result = toSnakeCase({ count: 42, active: true, data: null });
    expect(result.count).toBe(42);
    expect(result.active).toBe(true);
    expect(result.data).toBeNull();
  });
});

describe('toSnakeCaseArray', () => {
  it('converts each item in array', () => {
    const input = [
      { sourceSystem: 'image_2d' },
      { sourceSystem: 'three_d' },
    ];
    const result = toSnakeCaseArray(input);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ source_system: 'image_2d' });
    expect(result[1]).toEqual({ source_system: 'three_d' });
  });

  it('handles empty array', () => {
    expect(toSnakeCaseArray([])).toEqual([]);
  });
});
