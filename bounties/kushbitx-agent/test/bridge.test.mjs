import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import test from 'node:test';

import { KushBitxClient } from '@kushbitx/sdk';
import { runTool, TOOL_NAMES, TOKEN_ADDRESS } from '../src/bridge.mjs';

const SERVICE_RECIPIENT = '0x0d68028d06af13379C872FEE032568B4Be712f22';

function jsonResponse(body, status = 200, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', ...headers },
  });
}

test('tool boundary contains exactly the three read/evaluate/discover tools', async () => {
  assert.deepEqual(TOOL_NAMES, [
    'kushbitx_preview_token',
    'kushbitx_evaluate_spend',
    'kushbitx_discover_x402',
  ]);

  const source = await readFile(new URL('../src/bridge.mjs', import.meta.url), 'utf8');
  for (const forbidden of ['prepareRecovery(', 'submitPaidCheck(', 'restoreReport(', 'signTypedData', 'privateKey']) {
    assert.equal(source.includes(forbidden), false, `bridge must not expose ${forbidden}`);
  }
});

test('token preview uses the published SDK and sanitizes addresses', async () => {
  const client = new KushBitxClient({
    baseUrl: 'https://example.invalid',
    fetchFn: async (url, init) => {
      assert.equal(url, 'https://example.invalid/api/token-preview');
      assert.equal(init.method, 'POST');
      assert.deepEqual(JSON.parse(init.body), { chain: 'base', address: TOKEN_ADDRESS });
      return jsonResponse({ chain: 'base', address: TOKEN_ADDRESS, symbol: 'USDC', priceUsd: 1 });
    },
  });

  const result = await runTool('kushbitx_preview_token', {}, client);
  assert.equal(result.ok, true);
  assert.equal(result.preview.address, '<redacted-address>');
  assert.equal(result.preview.symbol, 'USDC');
});

test('SpendGuard evaluation is explicitly advisory and never authorizes execution', async () => {
  const client = new KushBitxClient({
    baseUrl: 'https://example.invalid',
    fetchFn: async (url, init) => {
      assert.equal(url, 'https://example.invalid/api/spendguard/evaluate');
      const body = JSON.parse(init.body);
      assert.equal(body.amount, '1.00');
      assert.equal(body.chain, 'base');
      assert.equal(body.asset, 'USDC');
      assert.equal(body.recipient, SERVICE_RECIPIENT);
      assert.equal(body.policy.maxPerTransaction, '5.00');
      assert.equal(body.policy.blockUnknownRecipients, true);
      return jsonResponse({ decision: 'HUMAN_APPROVAL', reason: 'threshold' });
    },
  });

  const result = await runTool('kushbitx_evaluate_spend', { amount: '1.00' }, client);
  assert.equal(result.ok, true);
  assert.equal(result.advisory, true);
  assert.equal(result.executionAuthorizedByThisTool, false);
  assert.equal(result.decision.decision, 'HUMAN_APPROVAL');
});

test('x402 discovery stops at a real HTTP 402 challenge and redacts payment addresses/header', async () => {
  const client = new KushBitxClient({
    baseUrl: 'https://example.invalid',
    fetchFn: async (url, init) => {
      assert.equal(url, 'https://example.invalid/api/token-risk');
      assert.deepEqual(JSON.parse(init.body), { chain: 'base', address: TOKEN_ADDRESS });
      return jsonResponse(
        {
          x402Version: 2,
          accepts: [
            {
              scheme: 'exact',
              network: 'eip155:8453',
              amount: '250000',
              asset: TOKEN_ADDRESS,
              payTo: SERVICE_RECIPIENT,
              maxTimeoutSeconds: 60,
              extra: { name: 'USD Coin', version: '2' },
            },
          ],
        },
        402,
        { 'PAYMENT-REQUIRED': 'opaque-test-header' },
      );
    },
  });

  const result = await runTool('kushbitx_discover_x402', {}, client);
  assert.equal(result.ok, true);
  assert.equal(result.stoppedAtPaymentChallenge, true);
  assert.equal(result.signed, false);
  assert.equal(result.paid, false);
  assert.equal(result.paymentHeaderPresent, true);
  assert.equal(result.challenge.network, 'eip155:8453');
  assert.equal(result.challenge.amount, '250000');
  assert.equal(result.challenge.asset, 'USD Coin');
  assert.equal(result.challenge.payTo, '<redacted-address>');
  assert.equal(JSON.stringify(result).includes('opaque-test-header'), false);
  assert.equal(JSON.stringify(result).includes(SERVICE_RECIPIENT), false);
});

test('challenge discovery fails closed if upstream does not return HTTP 402', async () => {
  const client = new KushBitxClient({
    baseUrl: 'https://example.invalid',
    fetchFn: async () => jsonResponse({ ok: true }, 200),
  });
  await assert.rejects(() => runTool('kushbitx_discover_x402', {}, client), /Expected an HTTP 402 payment challenge/);
});

test('upstream failures are surfaced instead of silently succeeding', async () => {
  const client = new KushBitxClient({
    baseUrl: 'https://example.invalid',
    fetchFn: async () => jsonResponse({ error: 'market data unavailable' }, 503),
  });
  await assert.rejects(() => runTool('kushbitx_preview_token', {}, client), /market data unavailable/);
});

test('invalid tool input and unknown tools fail before any payment-capable action', async () => {
  await assert.rejects(() => runTool('kushbitx_evaluate_spend', { amount: '-1' }, {}), /amount must be/);
  await assert.rejects(() => runTool('kushbitx_discover_x402', { service: 'preflight' }, {}), /only exposes the token-risk/);
  await assert.rejects(() => runTool('kushbitx_pay', {}, {}), /Unknown tool/);
});

async function startFakeService() {
  const server = createServer(async (req, res) => {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    const body = raw ? JSON.parse(raw) : {};
    const send = (status, data, headers = {}) => {
      res.writeHead(status, { 'content-type': 'application/json', ...headers });
      res.end(JSON.stringify(data));
    };

    if (req.url === '/api/token-preview') {
      assert.equal(body.address, TOKEN_ADDRESS);
      return send(200, { chain: 'base', address: TOKEN_ADDRESS, symbol: 'USDC', priceUsd: 1 });
    }
    if (req.url === '/api/spendguard/evaluate') {
      return send(200, { decision: 'HUMAN_APPROVAL', evaluated: true, recipient: body.recipient });
    }
    if (req.url === '/api/token-risk') {
      return send(
        402,
        {
          x402Version: 2,
          accepts: [{
            scheme: 'exact', network: 'eip155:8453', amount: '250000', asset: TOKEN_ADDRESS,
            payTo: SERVICE_RECIPIENT, maxTimeoutSeconds: 60, extra: { name: 'USD Coin', version: '2' },
          }],
        },
        { 'PAYMENT-REQUIRED': 'opaque-local-challenge' },
      );
    }
    return send(404, { error: 'not found' });
  });

  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  return { server, baseUrl: `http://127.0.0.1:${port}` };
}

function runAgent(baseUrl) {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', ['src/agent.py', '--base-url', baseUrl], {
      cwd: new URL('..', import.meta.url),
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

test('actual local ML agent chooses and executes the three safe SDK tools end to end', async (t) => {
  const { server, baseUrl } = await startFakeService();
  t.after(() => server.close());

  const result = await runAgent(baseUrl);
  assert.equal(result.code, 0, result.stderr);
  assert.match(result.stdout, /planner step 1: preview/);
  assert.match(result.stdout, /tool: kushbitx_preview_token/);
  assert.match(result.stdout, /tool: kushbitx_evaluate_spend/);
  assert.match(result.stdout, /tool: kushbitx_discover_x402/);
  assert.match(result.stdout, /planner step 4: finish/);
  assert.match(result.stdout, /"stoppedAtPaymentChallenge": true/);
  assert.match(result.stdout, /"signed": false/);
  assert.match(result.stdout, /"paid": false/);
  assert.match(result.stdout, /SpendGuard is advisory evaluation/);
  assert.equal(result.stdout.includes(SERVICE_RECIPIENT), false);
  assert.equal(result.stdout.includes('opaque-local-challenge'), false);
});
