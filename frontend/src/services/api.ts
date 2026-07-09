const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

/** Fetch JSON from the backend API. Throws on non-2xx responses. */
export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  return (await response.json()) as T
}
