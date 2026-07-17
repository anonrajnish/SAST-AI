// Unsafe deserialization: unserialize on untrusted data (CWE-502).
const { unserialize } = require("node-serialize");

function load(payload) {
  return unserialize(payload); // sast:vuln
}

module.exports = { load };
