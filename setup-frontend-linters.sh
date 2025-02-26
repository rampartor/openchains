#!/bin/bash

# Navigate to frontend directory
cd frontend

# Install ESLint and plugins
yarn add --dev eslint@8.57.0 \
  eslint-plugin-svelte@2.35.1 \
  @stylistic/eslint-plugin@1.7.0 \
  eslint-config-prettier@9.1.0

# Install Prettier and plugins
yarn add --dev prettier@3.2.4 \
  prettier-plugin-svelte@3.2.1

# Create ESLint config file
cat > .eslintrc.cjs << 'EOL'
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
  },
  overrides: [
    {
      files: ['*.svelte'],
      parser: 'svelte-eslint-parser',
    },
  ],
};
EOL

# Create Prettier config
cat > .prettierrc << 'EOL'
{
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true,
  "plugins": ["prettier-plugin-svelte"],
  "overrides": [{ "files": "*.svelte", "options": { "parser": "svelte" } }]
}
EOL

# Test if linting works
echo "Testing ESLint configuration..."
yarn eslint --ext .js,.svelte src/

echo "Setup complete for frontend linters!"
