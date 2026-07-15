// Reflected DOM XSS: user-controlled location.hash flows into innerHTML.
function render() {
  const output = document.getElementById("output");
  const value = decodeURIComponent(location.hash.slice(1));
  output.innerHTML = value; // sast:vuln  CWE-79 DOM-based XSS
}

render();
