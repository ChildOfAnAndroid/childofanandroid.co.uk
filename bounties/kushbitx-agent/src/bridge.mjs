import { KushBitxClient } from '@kushbitx/sdk';
import { randomUUID } from 'node:crypto';

export const TOKEN_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const DEFAULT_RECIPIENT = '0x0d68028d06af13379C872FEE032568B4Be712f22';
const ADDRESS_RE = /0x[a-fA-F0-9]{40}/g;

export const TOOL_NAMES = Object.freeze([
  'kushbitx_preview_token',
  'kushbitx_evaluate_spend',
  'kushbitx_discover_x402'
]);

function requiredString(value, name) {
  if (typeof value !== 'string' || value.trim() === '') throw new Error(`${name} must be a non-empty string`);
  return value.trim();
}

function decimalString(value, name) {
  const text = requiredString(String(value), name);
  if (!/^\d+(?:\.\d{1,6})?$/.test(text)) throw new Error(`${name} must be a non-negative decimal string`);
  return text;
}

export function sanitize(value, key = '') {
  if (key === 'paymentRequired') return value ? '<present-redacted>' : null;
  if (/^(?:recipient|payTo|from|to|address)$/i.test(key) && typeof value === 'string') return '<redacted-address>';
  if (/^(?:requestId|agentId)$/i.test(key) && typeof value === 'string') return '<redacted-id>';
  if (typeof value === 'string') return value.replace(ADDRESS_RE, '<redacted-address>');
  if (Array.isArray(value)) return value.map(item => sanitize(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, sanitize(v, k)]));
  }
  return value;
}

export function makeClient() {
  return new KushBitxClient({ baseUrl: process.env.KUSHBITX_BASE_URL || 'https://kushbitx.com' });
}

export async function runTool(name, args = {}, client = makeClient()) {
  if (!TOOL_NAMES.includes(name)) throw new Error(`Unknown tool: ${name}`);

  if (name === 'kushbitx_preview_token') {
    const address = args.address ? requiredString(args.address, 'address') : TOKEN_ADDRESS;
    const data = await client.previewToken(address);
    return sanitize({ tool: name, ok: true, preview: data });
  }

  if (name === 'kushbitx_evaluate_spend') {
    const amount = decimalString(args.amount ?? '1.00', 'amount');
    const recipient = args.recipient ? requiredString(args.recipient, 'recipient') : DEFAULT_RECIPIENT;
    const maxPerTransaction = decimalString(args.maxPerTransaction ?? '5.00', 'maxPerTransaction');
    const remainingDailyBudget = decimalString(args.remainingDailyBudget ?? '20.00', 'remainingDailyBudget');
    const requireHumanAbove = decimalString(args.requireHumanAbove ?? '2.00', 'requireHumanAbove');

    const input = {
      agentId: 'childofanandroid-kushbitx-agent',
      requestId: `bounty-${randomUUID()}`,
      amount,
      chain: 'base',
      asset: 'USDC',
      recipient,
      service: 'agent-demo',
      policy: {
        maxPerTransaction,
        remainingDailyBudget,
        requireHumanAbove,
        maxRepeats: 1,
        allowedRecipients: [recipient],
        blockUnknownRecipients: true
      },
      context: { repeatCount: 0, agentProofDecision: 'ALLOW' }
    };

    const decision = await client.evaluateSpend(input);
    return sanitize({
      tool: name,
      ok: true,
      advisory: true,
      executionAuthorizedByThisTool: false,
      decision
    });
  }

  const service = args.service ? requiredString(args.service, 'service') : 'token-risk';
  if (service !== 'token-risk') throw new Error('This no-pay integration only exposes the token-risk challenge');
  const address = args.address ? requiredString(args.address, 'address') : TOKEN_ADDRESS;
  const challenge = await client.getPaymentChallenge(service, { chain: 'base', address });

  const accepts = challenge.challenge?.accepts ?? challenge.challenge?.paymentRequirements?.accepts ?? [];
  const first = Array.isArray(accepts) ? accepts[0] : undefined;
  return sanitize({
    tool: name,
    ok: true,
    stoppedAtPaymentChallenge: true,
    signed: false,
    paid: false,
    service: challenge.service,
    path: challenge.path,
    paymentHeaderPresent: Boolean(challenge.paymentRequired),
    challenge: {
      x402Version: challenge.challenge?.x402Version,
      scheme: first?.scheme,
      network: first?.network,
      amount: first?.amount,
      asset: first?.extra?.name || first?.asset,
      maxTimeoutSeconds: first?.maxTimeoutSeconds,
      payTo: first?.payTo
    }
  });
}

async function main() {
  const [name, raw = '{}'] = process.argv.slice(2);
  if (!name) throw new Error(`Usage: node src/bridge.mjs <${TOOL_NAMES.join('|')}> '<json>'`);
  let args;
  try {
    args = JSON.parse(raw);
  } catch {
    throw new Error('Tool arguments must be valid JSON');
  }
  const result = await runTool(name, args);
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
