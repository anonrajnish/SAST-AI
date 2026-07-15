// Reflected DOM XSS in TypeScript: a query parameter flows into innerHTML.
function showQuery(container: HTMLElement): void {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") ?? "";
  container.innerHTML = query; // sast:vuln  CWE-79 DOM-based XSS
}

export { showQuery };
