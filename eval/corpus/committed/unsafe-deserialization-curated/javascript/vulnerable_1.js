// Unsafe deserialization: node-serialize unserialize on untrusted data (CWE-502).
const serialize = require("node-serialize");

function load(payload) {
  return serialize.unserialize(payload); // sast:vuln
}

module.exports = { load };
