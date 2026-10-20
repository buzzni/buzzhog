# posthog

A stripped-back Expo app over PostHog cloud tasks, built for a local stack.

## Local stack

In the posthog repo, once:

```bash
echo 'SANDBOX_PROVIDER=docker' >> .env
```

Then restart the stack. The login screen posts email and password to `/api/login/`, creates a personal API key for that user, and uses it as a bearer token from then on.

## Run

```bash
cd products/desktop
pnpm install
pnpm --filter @posthog/mobilehog ios     # first build
pnpm --filter @posthog/mobilehog start   # afterwards
```

The host lives in `src/config.ts`. Use your LAN IP instead of `localhost` on a real phone.

See [posthog release checks](../../../../docs/internal/mobilehog-release-checks.md) before you share a build.
