// Reverse tabnabbing: window.open with a computed URL and no noopener (CWE-1022).
const source = require("./source");

function openTab() {
  return window.open(source.getUrl(), "_blank"); // sast:vuln
}

module.exports = { openTab };
