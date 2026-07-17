// Safe: AES-GCM used for encryption (CWE-327).
const crypto = require("crypto");

function makeCipher(key, iv) {
  return crypto.createCipheriv("aes-256-gcm", key, iv); // sast:safe
}

module.exports = { makeCipher };
