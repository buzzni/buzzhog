**CORRECT usage pattern:**

<example>
User: How many weekly active users do we have?
Assistant: A weekly count is a governed shape, so the catalog comes first.
[Runs posthog:exec({ "command": "call metric-list {\"limit\": 100}" })]
Assistant: No approved metric covers weekly active users, so I fall through to the query tools and confirm the schema.
[Runs posthog:exec({ "command": "search query-trends" })]
Assistant: Let me check the tool description and schema.
[Runs posthog:exec({ "command": "info query-trends" })]
Assistant: I see query-trends needs `series` (array with hint). Let me get the full field schema.
[Runs posthog:exec({ "command": "schema query-trends series" })]
Assistant: Now I know the exact series structure. Let me construct the query.
[Runs posthog:exec({ "command": "call query-trends {...}" })]
</example>

<example>
User: Create a dashboard for our key revenue metrics
Assistant: I'll need dashboard and query tools. Let me search for them.
[Runs posthog:exec({ "command": "search dashboard" }) and posthog:exec({ "command": "search query-trends" }) in parallel]
Assistant: Let me check the schemas for the tools I'll need.
[Runs posthog:exec({ "command": "info dashboard-create" }) and posthog:exec({ "command": "info query-trends" }) in parallel]
Assistant: Now I have both schemas. Let me start by looking for existing revenue insights.
[Makes call commands with correct parameters]
</example>

**INCORRECT usage patterns — NEVER do this:**

<bad-example>
User: Show me our feature flags
Assistant: [Directly calls posthog:exec({ "command": "call feature-flag-get-all {}" }) with guessed parameters]
WRONG: Run `info feature-flag-get-all` once when its schema is missing.
</bad-example>

<bad-example>
User: Query our events
Assistant: [Calls three tools in parallel without any `info` calls first]
WRONG: Run `info` once for each missing schema.
</bad-example>

<bad-example>
User: Show me a trends chart of signups
Assistant: [Runs info query-trends, sees summary with hints, then immediately calls query-trends with guessed series structure]
WRONG — info returned a summary with hint: "DO NOT GUESS – run `schema query-trends series` before populating this field".
You MUST follow the hint and run `schema` before constructing the series field.
</bad-example>
