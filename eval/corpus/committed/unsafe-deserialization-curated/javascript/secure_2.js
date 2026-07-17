// Safe deserialization: JSON.parse cannot instantiate arbitrary objects (CWE-502 safe).
const source = require("./source");

function load(req) {
  return JSON.parse(req.body); // sast:safe
}

module.exports = { load, source };
