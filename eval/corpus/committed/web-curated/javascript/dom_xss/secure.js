// Safe: user-controlled input is written via textContent (no HTML parsing).
function render() {
  const output = document.getElementById("output");
  const value = decodeURIComponent(location.hash.slice(1));
  output.textContent = value; // sast:safe  textContent does not execute markup
}

render();
