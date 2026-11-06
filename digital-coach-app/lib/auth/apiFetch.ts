import { auth } from "@App/lib/firebase/firebase.config";

/** Browser-side authenticated calls to the FastAPI backend. */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const user = auth.currentUser;
  if (!user) throw new Error("Sign in before calling the API");
  const token = await user.getIdToken();
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...init, headers });
}
