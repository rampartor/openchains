module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:svelte/recommended',
    'prettier',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['@stylistic'],
  rules: {
    '@stylistic/indent': ['error', 2],
    '@stylistic/linebreak-style': ['error', 'unix'],
    '@stylistic/quotes': ['error', 'single', { 'avoidEscape': true }],
    '@stylistic/semi': ['error', 'always'],
    'no-unused-vars': ['warn'],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'max-len': ['error', { 'code': 120 }],
  },
  overrides: [
    {
      files: ['*.svelte'],
      parser: 'svelte-eslint-parser',
    },
  ],
};
