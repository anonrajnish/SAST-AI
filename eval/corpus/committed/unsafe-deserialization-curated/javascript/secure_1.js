// Safe deserialization: JSON.parse only parses data (CWE-502 safe).
const source = require("./source");

function load(payload) {
  return JSON.parse(payload); // sast:safe
}

module.exports = { load, source };
