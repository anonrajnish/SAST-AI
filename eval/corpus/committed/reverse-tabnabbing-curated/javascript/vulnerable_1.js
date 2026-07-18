// Reverse tabnabbing: window.open with _blank and no noopener (CWE-1022).
const url = "https://external.example.com";

function openTab() {
  return window.open(url, "_blank"); // sast:vuln
}

module.exports = { openTab };
