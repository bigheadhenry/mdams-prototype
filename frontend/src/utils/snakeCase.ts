/**
 * 驼峰命名转下划线命名（用于前端 → 后端 API 数据契约对齐）
 *
 * 后端 Cart API 使用 snake_case（如 source_system, object_number）
 * 前端 TypeScript 类型使用 camelCase（如 sourceSystem, objectNumber）
 *
 * 此工具函数在调用后端 API 前转换字段名。
 */

type RecordOfAny = Record<string, unknown>;

/** 将 camelCase 对象的 key 转换为 snake_case */
export function toSnakeCase<T extends RecordOfAny>(obj: T): RecordOfAny {
  const result: RecordOfAny = {};
  for (const [key, value] of Object.entries(obj)) {
    result[camelToSnake(key)] = value;
  }
  return result;
}

/** 将数组中的每个 camelCase 对象转换为 snake_case */
export function toSnakeCaseArray<T extends RecordOfAny>(arr: T[]): RecordOfAny[] {
  return arr.map(toSnakeCase);
}

/** 单字段 camelCase → snake_case 转换 */
function camelToSnake(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}
