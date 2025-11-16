import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/**/*.test.ts', 'src/**/*.spec.ts'],
    exclude: ['node_modules/', 'dist/', 'test/**/*.mjs', 'test/**/*.js'],
    env: {
      NODE_ENV: 'test',
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'src/__tests__/',
        'test/',
        '*.config.*',
        '*.test.*',
        '*.spec.*'
      ]
    }
  }
});
