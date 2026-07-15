// Eval injection: an untrusted query parameter is passed to eval().
function compute(expression) {
  // expression originates from location.search in the caller.
  return eval(expression); // sast:vuln  CWE-95 eval injection
}

export { compute };
