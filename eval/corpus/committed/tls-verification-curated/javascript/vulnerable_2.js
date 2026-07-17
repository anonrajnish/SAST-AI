// TLS verification disabled: request options with rejectUnauthorized false (CWE-295).
const https = require("https");

function request(path) {
  const opts = { path, rejectUnauthorized: false }; // sast:vuln
  return https.request(opts);
}

module.exports = { request };
