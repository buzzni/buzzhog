import { fetch } from "expo/fetch";
import * as SecureStore from "expo-secure-store";
import { create } from "zustand";
import { POSTHOG_HOST } from "@/config";
import {
  CLOUD_HOSTS,
  type CloudRegion,
  OAUTH_SCOPE_VERSION,
  refreshOAuth,
  type SignInOptions,
  signInWithOAuth,
} from "@/lib/oauth";

const SESSION_KEY = "mobilehog_session";

export type Region = "local" | CloudRegion;

export interface Session {
  region: Region;
  host: string;
  apiKey: string;
  // OAuth sessions only; a local personal API key never expires.
  refreshToken?: string;
  expiresAt?: number;
  // The projects an OAuth token may reach; empty or missing means no limit.
  scopedTeams?: number[];
  scopeVersion?: number;
  projectId: number;
  projectName: string;
  userId: number;
  userName: string;
  email?: string;
}

interface AuthState {
  session: Session | null;
  hydrated: boolean;
  generation: number;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  loginWithOAuth: (
    region: CloudRegion,
    options?: SignInOptions,
  ) => Promise<void>;
  // Swaps an expired OAuth access token; returns the new bearer.
  refresh: () => Promise<string>;
  selectProject: (projectId: number, projectName: string) => Promise<void>;
  logout: () => Promise<void>;
}

async function readJson<T>(response: Response, what: string): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let detail = text;
    try {
      const parsed = JSON.parse(text);
      detail = parsed.detail ?? parsed.error ?? text;
    } catch {}
    throw new Error(`${what} failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as T;
}

const LOCAL_KEY_LABEL = "mobilehog local";

// Django rejects a CSRF cookie that is not 32 or 64 letters and digits, and
// reads it only under CSRF_COOKIE_NAME (posthog_csrftoken). With the cookie jar
// off, the app sends this value as both the cookie and the header, which
// satisfies the double-submit check.
const LOCAL_CSRF_TOKEN = "mobilehoglocalcsrfmobilehoglocal";

// Log in without touching the cookie jar (a stale session there would trip the
// CSRF check), pull the session id out of the response, and swap it for the
// app's personal API key, so every later call is a plain bearer.
async function loginWithPassword(
  email: string,
  password: string,
): Promise<Session> {
  const loginResponse = await fetch(`${POSTHOG_HOST}/api/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "omit",
  });
  await readJson<{ success?: boolean }>(loginResponse, "Login");
  const sessionId = /sessionid=([^;,\s]+)/.exec(
    loginResponse.headers.get("set-cookie") ?? "",
  )?.[1];
  if (!sessionId) {
    throw new Error("Login succeeded but no session cookie came back.");
  }

  const sessionHeaders = {
    "Content-Type": "application/json",
    Cookie: `sessionid=${sessionId}; posthog_csrftoken=${LOCAL_CSRF_TOKEN}`,
    "X-CSRFToken": LOCAL_CSRF_TOKEN,
    // Over HTTPS, Django also requires a same-origin Referer when the request
    // has no Origin header, and native fetch sends neither.
    Referer: `${POSTHOG_HOST}/`,
  };
  const keysResponse = await fetch(`${POSTHOG_HOST}/api/personal_api_keys/`, {
    headers: sessionHeaders,
    credentials: "omit",
  });
  const keys = await readJson<Array<{ id: string; label: string }>>(
    keysResponse,
    "Reading API keys",
  );
  // Roll the key that an earlier login made instead of minting another one.
  // The server caps each user at 10 personal API keys and logout cannot revoke
  // a key, so a new key per login would block login once the user hits the cap.
  const existing = keys.find((key) => key.label === LOCAL_KEY_LABEL);
  const keyResponse = await fetch(
    existing
      ? `${POSTHOG_HOST}/api/personal_api_keys/${existing.id}/roll/`
      : `${POSTHOG_HOST}/api/personal_api_keys/`,
    {
      method: "POST",
      headers: sessionHeaders,
      body: JSON.stringify(
        existing
          ? {}
          : {
              label: LOCAL_KEY_LABEL,
              scopes: ["*"],
              scoped_teams: [],
              scoped_organizations: [],
            },
      ),
      credentials: "omit",
    },
  );
  const minted = await readJson<{ value?: string | null }>(
    keyResponse,
    existing ? "Rolling API key" : "Creating API key",
  );
  const apiKey = minted.value;
  if (!apiKey) {
    throw new Error(
      "The server did not return a personal API key. Check that your local stack runs the latest code, then sign in again.",
    );
  }

  return describeSession({ region: "local", host: POSTHOG_HOST, apiKey });
}

async function describeSession(base: {
  region: Region;
  host: string;
  apiKey: string;
  refreshToken?: string;
  expiresAt?: number;
  projectId?: number;
}): Promise<Session> {
  const meResponse = await fetch(`${base.host}/api/users/@me/`, {
    headers: { Authorization: `Bearer ${base.apiKey}` },
    credentials: "omit",
  });
  const me = await readJson<{
    id: number;
    first_name: string;
    email: string;
    team?: { id: number; name: string } | null;
  }>(meResponse, "Loading user");
  const projectId = base.projectId ?? me.team?.id;
  if (!projectId) {
    throw new Error("This user has no current project.");
  }
  let projectName = me.team?.id === projectId ? me.team.name : null;
  if (!projectName) {
    const projectResponse = await fetch(
      `${base.host}/api/projects/${projectId}/`,
      {
        headers: { Authorization: `Bearer ${base.apiKey}` },
        credentials: "omit",
      },
    );
    projectName =
      (await readJson<{ name?: string }>(projectResponse, "Loading project"))
        .name ?? `Project ${projectId}`;
  }
  return {
    ...base,
    projectId,
    projectName,
    userId: me.id,
    userName: me.first_name || me.email,
    email: me.email,
  };
}

let storageWrite: Promise<void> = Promise.resolve();
let loginPending = false;

function queueStorageWrite<T>(write: () => Promise<T>): Promise<T> {
  const pending = storageWrite.then(write);
  storageWrite = pending.then(
    () => {},
    () => {},
  );
  return pending;
}

export function sessionIdentity(state = useAuth.getState()): string {
  const { session, generation } = state;
  return JSON.stringify([
    generation,
    session?.host,
    session?.projectId,
    session?.userId,
  ]);
}

export function accountStorageKey(prefix: string): string {
  const session = requireSession();
  const host = Array.from(session.host, (character) =>
    character.charCodeAt(0).toString(16),
  ).join("-");
  return `${prefix}_${host}_${session.projectId}_${session.userId}`;
}

export const useAuth = create<AuthState>((set, get) => {
  // The builder runs inside the queued write so it sees every earlier commit,
  // such as a token refresh that finished while a project switch waited.
  const commit = async (
    build: (current: Session | null) => Session,
    generation: number,
  ): Promise<Session> => {
    return queueStorageWrite(async () => {
      if (get().generation !== generation)
        throw new Error("Session changed. Sign in again.");
      const session = build(get().session);
      await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(session));
      if (get().generation !== generation)
        throw new Error("Session changed. Sign in again.");
      set({ session, hydrated: true });
      return session;
    });
  };

  const login = async (attempt: () => Promise<Session>): Promise<void> => {
    if (loginPending) return;
    loginPending = true;
    if (get().session || !get().hydrated) {
      set({ session: null, generation: get().generation + 1, hydrated: true });
    }
    const generation = get().generation;
    try {
      const session = await attempt();
      await commit(() => session, generation);
    } finally {
      loginPending = false;
    }
  };

  return {
    session: null,
    hydrated: false,
    generation: 0,

    hydrate: async () => {
      if (get().hydrated) return;
      const generation = get().generation;
      try {
        const raw = await SecureStore.getItemAsync(SESSION_KEY);
        if (get().generation !== generation || get().session) return;
        const session = raw ? (JSON.parse(raw) as Session) : null;
        if (
          session &&
          session.region !== "local" &&
          session.scopeVersion !== OAUTH_SCOPE_VERSION
        ) {
          await SecureStore.deleteItemAsync(SESSION_KEY);
          if (get().generation === generation && !get().session) {
            set({ session: null, hydrated: true });
          }
          return;
        }
        set({ session, hydrated: true });
      } catch {
        if (get().generation === generation) set({ hydrated: true });
      }
    },

    login: (email, password) => login(() => loginWithPassword(email, password)),

    loginWithOAuth: (region, options) =>
      login(async () => {
        const tokens = await signInWithOAuth(region, options);
        const session = await describeSession({
          region,
          host: CLOUD_HOSTS[region],
          apiKey: tokens.access_token,
          refreshToken: tokens.refresh_token,
          expiresAt: Date.now() + tokens.expires_in * 1000,
          projectId: tokens.scoped_teams?.[0],
        });
        return {
          ...session,
          scopedTeams: tokens.scoped_teams,
          scopeVersion: OAUTH_SCOPE_VERSION,
        };
      }),

    refresh: async () => {
      const { session: current, generation } = get();
      if (!current?.refreshToken || current.region === "local") {
        throw new Error("Session cannot be refreshed");
      }
      const tokens = await refreshOAuth(current.region, current.refreshToken);
      const session = await commit((latest) => {
        if (!latest || latest.refreshToken !== current.refreshToken)
          throw new Error("Session changed. Sign in again.");
        return {
          ...latest,
          apiKey: tokens.access_token,
          refreshToken: tokens.refresh_token || current.refreshToken,
          expiresAt: Date.now() + tokens.expires_in * 1000,
          scopedTeams: tokens.scoped_teams ?? latest.scopedTeams,
        };
      }, generation);
      return session.apiKey;
    },

    selectProject: async (projectId, projectName) => {
      const current = get().session;
      if (!current || current.projectId === projectId) return;
      await commit((latest) => {
        if (!latest) throw new Error("Session changed. Sign in again.");
        return { ...latest, projectId, projectName };
      }, get().generation);
    },

    logout: async () => {
      set({ session: null, generation: get().generation + 1, hydrated: true });
      await queueStorageWrite(() => SecureStore.deleteItemAsync(SESSION_KEY));
    },
  };
});

export function requireSession(): Session {
  const { session } = useAuth.getState();
  if (!session) {
    throw new Error("Not signed in");
  }
  return session;
}
