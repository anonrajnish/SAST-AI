// Safe: window.open with noopener prevents opener access (CWE-1022 safe).
const url = "https://external.example.com";

function openTab() {
  return window.open(url, "_blank", "noopener"); // sast:safe
}

module.exports = { openTab };
