import path from 'node:path';
import js from '@eslint/js';
import stylistic from '@stylistic/eslint-plugin';
import pluginVue from 'eslint-plugin-vue';
import { createNodeResolver, flatConfigs as importXConfigs } from 'eslint-plugin-import-x';
import tseslint from 'typescript-eslint';
import globals from 'globals';

const aliasResolver = createNodeResolver({
  alias: {
    '@': [path.resolve(import.meta.dirname, 'src')],
  },
  extensions: ['.js', '.jsx', '.ts', '.tsx', '.vue', '.json'],
});

const stylisticConfig = stylistic.configs.customize({
  braceStyle: '1tbs',
  indent: 2,
  jsx: false,
  quotes: 'single',
  semi: true,
  commaDangle: 'always-multiline',
  arrowParens: true,
});

const attributesOrder = [
  'DEFINITION',
  'LIST_RENDERING',
  'CONDITIONALS',
  'RENDER_MODIFIERS',
  'GLOBAL',
  'UNIQUE',
  'TWO_WAY_BINDING',
  'OTHER_DIRECTIVES',
  'ATTR_DYNAMIC',
  'ATTR_STATIC',
  'ATTR_SHORTHAND_BOOL',
  'EVENTS',
  'CONTENT',
];

export default [
  {
    ignores: ['dist/**', 'api-mocker/**', 'src/components/ui/**'],
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  importXConfigs.recommended,
  stylisticConfig,
  {
    // <script setup lang="ts"> блоки .vue парсятся TS-парсером
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },
  {
    files: ['src/**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.node,
        ...globals.browser,
        defineModel: 'readonly',
      },
    },
    settings: {
      'import-x/resolver-next': [aliasResolver],
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/valid-v-slot': ['error', { allowModifiers: true }],
      'max-len': ['error', { code: 120, ignoreStrings: true }],
      'vue/max-len': ['error', { code: 120, ignoreStrings: true }],
      'no-console': ['warn', { allow: ['error'] }],
      'vue/attributes-order': ['warn', { order: attributesOrder, alphabetical: false }],
      'vue/padding-line-between-tags': ['error', [
        { blankLine: 'always', prev: '*:single-line', next: '*:multi-line' },
        { blankLine: 'always', prev: '*:multi-line', next: '*:single-line' },
        { blankLine: 'always', prev: '*:multi-line', next: '*:multi-line' },
        { blankLine: 'never', prev: '*:single-line', next: '*:single-line' },
      ]],
    },
  },
];
