import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(__dirname, '..');
const read = (relativePath: string) => fs.readFileSync(path.join(srcRoot, relativePath), 'utf8');

describe('M6 UI design-token integration contract', () => {
  it('imports the extracted MDAMS theme tokens at app entry', () => {
    expect(read('main.tsx')).toContain("./styles/mdams-theme.css");
  });

  it('defines the required token utility classes', () => {
    const css = read('styles/mdams-theme.css');
    ['--mdams-sidebar-gradient', '.mdams-stat-card', '.mdams-table-dense', '.mdams-toolbar', '.mdams-content'].forEach((token) => {
      expect(css).toContain(token);
    });
  });

  it('applies tokens to the three high-frequency pages', () => {
    const app = read('App.tsx');
    const directory = read('components/PlatformDirectory.tsx');
    expect(app).toContain('mdams-stat-card');
    expect(app).toContain('mdams-table-dense');
    expect(directory).toContain('mdams-toolbar');
    expect(directory).toContain('mdams-table-dense');
    expect(directory).toContain('mdams-stat-card');
  });
});
