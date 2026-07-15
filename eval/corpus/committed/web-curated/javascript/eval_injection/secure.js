// Safe: untrusted input is parsed with JSON.parse instead of eval().
function compute(payload) {
  // payload originates from location.search in the caller.
  return JSON.parse(payload); // sast:safe  JSON.parse does not execute code
}

export { compute };
