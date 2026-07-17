// TLS verification disabled: https.Agent with rejectUnauthorized false (CWE-295).
const https = require("https");

function agent() {
  return new https.Agent({ rejectUnauthorized: false }); // sast:vuln
}

module.exports = { agent };
