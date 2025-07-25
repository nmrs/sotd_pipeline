module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react', '@typescript-eslint', 'react-hooks', 'prettier'],
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // Basic rules to start with
    'no-console': 'off',
    'prettier/prettier': 'error',
    'react/prop-types': 'off',
    // Disable React JSX scope requirement for test files
    'react/react-in-jsx-scope': 'off',
  },
  ignorePatterns: ['dist/', 'node_modules/', 'coverage/', 'build/', '.next/', 'out/', '*.min.js'],
};
