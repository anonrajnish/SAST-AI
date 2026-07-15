// Hardcoded secret: a live-looking API key is embedded in client-side source.
const STRIPE_SECRET_KEY = "sk_live_EXAMPLE_do_not_use_0123456789abcd"; // sast:vuln  CWE-798

export function authHeader(): Record<string, string> {
  return { Authorization: `Bearer ${STRIPE_SECRET_KEY}` };
}
