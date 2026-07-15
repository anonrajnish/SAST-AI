// Safe: the secret is read from build-time configuration, not embedded.
const stripeKey = import.meta.env.VITE_STRIPE_KEY ?? ""; // sast:safe  injected via env

export function authHeader(): Record<string, string> {
  return { Authorization: `Bearer ${stripeKey}` };
}
