// Safe TLS: https.Agent keeps certificate verification enabled (CWE-295 safe).
const https = require("https");

function agent() {
  return new https.Agent({ rejectUnauthorized: true }); // sast:safe
}

module.exports = { agent };
