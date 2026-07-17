// Weak hash: MD5 used to hash data (CWE-328).
const crypto = require("crypto");

function digest(data) {
  return crypto.createHash("md5").update(data).digest("hex"); // sast:vuln
}

module.exports = { digest };
