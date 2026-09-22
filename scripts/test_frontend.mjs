import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const directory = mkdtempSync(join(tmpdir(), 'coaa-api-tests-'));
try {
  const compile = spawnSync('tsc', ['src/api.ts', '--target', 'ES2022', '--module', 'ES2022',
    '--lib', 'ES2022,DOM', '--strict', '--skipLibCheck', '--outDir', directory], { stdio: 'inherit' });
  if (compile.error) throw compile.error;
  if (compile.status !== 0) throw new Error('API typecheck failed');
  const modulePath = join(directory, 'api.mjs');
  writeFileSync(modulePath, readFileSync(join(directory, 'api.js')));
  const tests = spawnSync(process.execPath, ['--test', 'tests/frontend.test.mjs'], {
    stdio: 'inherit', env: { ...process.env, BBY_API_TEST_MODULE: pathToFileURL(modulePath).href },
  });
  if (tests.error) throw tests.error;
  process.exitCode = tests.status ?? 1;
} finally {
  rmSync(directory, { recursive: true, force: true });
}
