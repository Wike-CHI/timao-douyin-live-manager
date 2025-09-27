// ESLint flat config for this monorepo
// - Lint Electron main/preload JS files
// - Ignore TypeScript/TSX in renderer for now (handled by TypeScript compiler)
// If you want TS linting, install @typescript-eslint/* and extend config accordingly.

import js from '@eslint/js';
import globals from 'globals';

export default [
  // Global ignores
  {
    ignores: [
      '**/node_modules/**',
      'dist/**',
      'frontend/**',
      'records/**',
      // Ignore renderer TypeScript for now (no TS ESLint plugins installed yet)
      'electron/renderer/**',
    ],
  },

  // Base JS recommended rules
  js.configs.recommended,

  // Electron main/preload JS
  {
    files: ['electron/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: globals.node,
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-console': 'off',
      'no-async-promise-executor': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
  // Electron preload runs in a hybrid context (renderer-like + Node APIs)
  {
    files: ['electron/preload.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
  },
];
