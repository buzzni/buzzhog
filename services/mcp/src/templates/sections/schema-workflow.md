#### Read the query guidance

Before selecting a query method, read the `querying-posthog-data` skill once if it is installed. Follow its query-selection guidance and relevant examples. It is a built-in PostHog skill, not a team skill: do not fetch it with `skill-get`. If it is not installed, use the available tool descriptions.

#### Insight query workflow

Construct a minimal query with the selected tool. Include only the filters, breakdowns, and settings required for the answer. Execute the query and analyze the result. Save an insight or add it to a dashboard when the user requests it.

For complex investigations, combine multiple query types. For example, use `query-trends` to identify when a metric changed, then `query-funnel` to check if conversion was affected, then `query-trends` with breakdowns to isolate the segment.
