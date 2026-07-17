// Weak cipher: DES used for encryption (CWE-327).
const crypto = require("crypto");

function makeCipher(key, iv) {
  return crypto.createCipheriv("des-cbc", key, iv); // sast:vuln
}

module.exports = { makeCipher };
