// Safe: the query parameter is rendered with textContent, which is inert.
function showQuery(container: HTMLElement): void {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") ?? "";
  container.textContent = query; // sast:safe  textContent does not parse HTML
}

export { showQuery };
