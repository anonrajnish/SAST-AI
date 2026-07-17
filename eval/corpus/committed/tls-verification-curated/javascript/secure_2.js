// Safe TLS: default agent verifies certificates (CWE-295 safe).
const https = require("https");

function agent() {
  return new https.Agent({}); // sast:safe
}

module.exports = { agent };
