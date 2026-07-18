// Safe: window.open with noopener,noreferrer prevents opener access (CWE-1022 safe).
const url = "https://external.example.com";

function openTab() {
  return window.open(url, "_blank", "noopener,noreferrer"); // sast:safe
}

module.exports = { openTab };
