const { spawnSync } = require('node:child_process');
const path = require('node:path');
const dotenv = require('dotenv');

const nestApiRoot = path.resolve(__dirname, '..');
const backendRoot = path.resolve(nestApiRoot, '..');
const envPath = path.join(backendRoot, '.env');

dotenv.config({ path: envPath });

const prismaEntrypoint = path.join(
  nestApiRoot,
  'node_modules',
  'prisma',
  'build',
  'index.js',
);
const prismaArgs = process.argv.slice(2);
const result = spawnSync(process.execPath, [prismaEntrypoint, ...prismaArgs], {
  cwd: nestApiRoot,
  env: process.env,
  stdio: 'inherit',
});

if (typeof result.status === 'number') {
  process.exit(result.status);
}

if (result.error) {
  throw result.error;
}

process.exit(1);
