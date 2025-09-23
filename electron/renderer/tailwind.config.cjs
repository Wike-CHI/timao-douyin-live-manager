const { join } = require('path');

module.exports = {
  content: [join(__dirname, 'index.html'), join(__dirname, 'src/**/*.{ts,tsx,js,jsx}')],
  theme: {
    extend: {},
  },
  plugins: [],
};
