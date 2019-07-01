/*eslint-env node*/
module.exports = {
  processors: ['stylelint-processor-styled-components'],
  extends: [
    'stylelint-config-recommended',
    'stylelint-config-prettier',
    'stylelint-config-styled-components',
  ],
  rules: {
    'declaration-colon-newline-after': null,
    'block-no-empty': null,
    'selector-type-no-unknown': [true, {ignoreTypes: ['$dummyValue']}],
  },
};
