import typescript from 'rollup-plugin-typescript2';
import nodeResolve from 'rollup-plugin-node-resolve';
import commonjs from 'rollup-plugin-commonjs';
import sourcemaps from 'rollup-plugin-sourcemaps';

import pkg from './package.json'

export default {
  input: 'app.ts',
  output: [
    {
      file: pkg.main,
      format: 'iife',
      sourcemap: true,
    },
  ],
  external: [
  ],
  plugins: [
    nodeResolve({
      jsnext: true
    }),
    commonjs({
    }),
    typescript({
      typescript: require('typescript'),
    }),
    sourcemaps(),
  ],
}
