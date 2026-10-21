import { beforeEach, describe, expect, it, vi } from "vitest";

const secureStore = vi.hoisted(() => ({
  deleteItemAsync: vi.fn(),
  getItemAsync: vi.fn(),
  setItemAsync: vi.fn(),
}));

vi.mock("expo/fetch", () => ({ fetch: vi.fn() }));
vi.mock("expo-secure-store", () => secureStore);
vi.mock("expo-auth-session", () => ({}));
vi.mock("expo-web-browser", () => ({ maybeCompleteAuthSession: vi.fn() }));

import { fetch } from "expo/fetch";
import { type Session, useAuth } from "./auth";

interface FakeKey {
  id: string;
  label: string;
  value: string;
}

function reply(status: number, body: unknown, headers: HeadersInit = {}) {
  return {
    ok: status < 300,
    status,
    headers: new Headers(headers),
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

// Answers the way the local Django stack does for the calls a password login
// makes, including the CSRF check, the required create fields and the key cap.
function fakeLocalStack(keys: FakeKey[]) {
  let minted = 0;
  const mint = () => `phx_minted_${++minted}`;
  vi.mocked(fetch).mockImplementation((async (
    url: string,
    init: {
      method?: string;
      headers?: Record<string, string>;
      body?: string;
    } = {},
  ) => {
    const path = new URL(url).pathname;
    const method = init.method ?? "GET";
    const headers = init.headers ?? {};
    if (path === "/api/login/") {
      return reply(200, { success: true }, { "set-cookie": "sessionid=s1" });
    }
    if (path === "/api/users/@me/") {
      const bearer = headers.Authorization?.replace("Bearer ", "");
      return keys.some((key) => key.value === bearer)
        ? reply(200, {
            id: 7,
            first_name: "Pat",
            email: "pat@example.com",
            team: { id: 42, name: "Demo project" },
          })
        : reply(401, { detail: "Invalid token" });
    }
    const cookies = new Map(
      (headers.Cookie ?? "").split("; ").map((pair) => {
        const [name, ...value] = pair.split("=");
        return [name, value.join("=")] as const;
      }),
    );
    if (cookies.get("sessionid") !== "s1") {
      return reply(401, { detail: "Not logged in" });
    }
    if (method !== "GET") {
      const csrf = cookies.get("posthog_csrftoken");
      if (
        !csrf ||
        !/^[a-zA-Z0-9]{32}$/.test(csrf) ||
        headers["X-CSRFToken"] !== csrf
      ) {
        return reply(403, { detail: "CSRF Failed" });
      }
    }
    if (path === "/api/personal_api_keys/" && method === "GET") {
      return reply(
        200,
        keys.map(({ id, label }) => ({ id, label })),
      );
    }
    if (path === "/api/personal_api_keys/" && method === "POST") {
      const body = JSON.parse(init.body ?? "{}");
      for (const field of [
        "label",
        "scopes",
        "scoped_teams",
        "scoped_organizations",
      ]) {
        if (!(field in body)) {
          return reply(400, { detail: "This field is required." });
        }
      }
      if (keys.length >= 10) {
        return reply(400, { detail: "You can only have 10 keys." });
      }
      const key = { id: `k${keys.length}`, label: body.label, value: mint() };
      keys.push(key);
      return reply(201, { id: key.id, value: key.value });
    }
    const roll = /^\/api\/personal_api_keys\/([^/]+)\/roll\/$/.exec(path);
    const rolled = keys.find((key) => key.id === roll?.[1]);
    if (rolled && method === "POST") {
      rolled.value = mint();
      return reply(200, { id: rolled.id, value: rolled.value });
    }
    return reply(404, { detail: "Not found" });
  }) as unknown as typeof fetch);
}

const savedSession: Session = {
  region: "us",
  host: "https://us.posthog.com",
  apiKey: "old-access-token",
  refreshToken: "old-refresh-token",
  expiresAt: Date.now() + 60_000,
  scopedTeams: [42],
  projectId: 42,
  projectName: "Demo project",
  userId: 7,
  userName: "Pat",
};

describe("mobilehog auth", () => {
  beforeEach(() => {
    secureStore.deleteItemAsync.mockReset();
    secureStore.getItemAsync.mockReset();
    secureStore.setItemAsync.mockReset();
    useAuth.setState({ session: null, hydrated: false, generation: 0 });
  });

  it("forces an existing OAuth session to reauthorize after scopes change", async () => {
    secureStore.getItemAsync.mockResolvedValue(JSON.stringify(savedSession));

    await useAuth.getState().hydrate();

    expect(secureStore.deleteItemAsync).toHaveBeenCalledWith(
      "mobilehog_session",
    );
    expect(useAuth.getState()).toMatchObject({
      session: null,
      hydrated: true,
    });
  });

  it("signs in with a password past the key cap and keeps a single app key", async () => {
    const ownKeys = Array.from({ length: 9 }, (_, index) => ({
      id: `own${index}`,
      label: `Own key ${index}`,
      value: `phx_own_${index}`,
    }));
    const keys = [...ownKeys];
    fakeLocalStack(keys);

    for (let attempt = 0; attempt < 3; attempt++) {
      await useAuth.getState().login("pat@example.com", "password");
    }

    const appKeys = keys.filter((key) => key.label === "mobilehog local");
    expect(appKeys).toHaveLength(1);
    expect(useAuth.getState().session).toMatchObject({
      region: "local",
      apiKey: appKeys[0].value,
      projectId: 42,
    });
    expect(keys.slice(0, ownKeys.length)).toEqual(ownKeys);
  });
});
