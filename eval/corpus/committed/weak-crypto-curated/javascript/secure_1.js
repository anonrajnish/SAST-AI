// Safe: SHA-256 used to hash data (CWE-328).
const crypto = require("crypto");

function digest(data) {
  return crypto.createHash("sha256").update(data).digest("hex"); // sast:safe
}

module.exports = { digest };
