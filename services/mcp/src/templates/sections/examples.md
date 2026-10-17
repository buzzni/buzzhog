### Examples

#### Creating an insight with segmentation

<example>
User: How many users have chatted with the AI assistant from the US?
Assistant: I'll help you find the number of users who have chatted with the AI assistant from the US.
1. Run the query for "chatted with the AI assistant" events, filtered to users from the US (the `query-trends` tool or the appropriate query tool)
2. Analyze retrieved data and provide a concise summary
*Begins working on the first task*
<reasoning>
1. Creating an insight requires the events and properties relevant to the user's query.
2. The user query requests additional segmentation by country.
</reasoning>
</example>

#### Investigating a metric change

<example>
User: Check why onboarding completion rate has dropped and if it is connected with a low sign-up count.
Assistant: I'll help you analyze the reasons why the metrics have changed. Let me break this down into steps.
1. Check the governed catalog for an approved onboarding conversion metric (the `metric-list` tool); run it with `data-catalog-metric-run` if one matches, otherwise continue
2. Run a trends query for the onboarding completion event to confirm the drop and identify when it started (the `query-trends` tool)
3. Run a trends query for the sign-up event to check if sign-up counts have also changed (the `query-trends` tool)
4. Run trends queries with breakdowns (e.g., by country, device, or referral source) to identify which segments are affected (the `query-trends` tool)
5. Run a funnel to check the conversion rate between sign-up and onboarding completion (the `query-funnel` tool)
6. Synthesize findings across all queries and explain whether the metrics are correlated
*Begins working on the first task*
<reasoning>
1. A conversion rate is a governed shape, so the catalog is checked before any query.
2. The user requested analysis of multiple metrics that must be investigated separately.
2. Multiple queries are needed to understand each trend independently.
3. Breakdowns help isolate the root cause by identifying affected segments.
4. A funnel connects the two metrics to check for a direct relationship.
</reasoning>
</example>

#### Building a dashboard

<example>
User: Generate a revenue dashboard.
Assistant: I'll help you create a revenue dashboard. Let me plan the steps.
1. List existing dashboards to check if one already covers revenue (the `dashboards-get-all` tool)
2. Search saved insights related to revenue (the `insights-list` tool)
3. Validate promising insights by reading their query schemas (the `insight-get` tool)
4. Create new insights only for metrics not covered by existing insights (the `query-trends` tool or appropriate query tool)
5. Create a new dashboard with both existing and newly created insights (the `dashboard-create` tool)
6. Analyze the created dashboard and provide a concise summary of metrics
*Begins working on the first task*
<reasoning>
1. The user requested creating a dashboard. This is a complex task that requires multiple steps to complete.
2. Finding existing insights requires both listing (to discover insights with different naming) and searching.
3. Promising insights must be validated by reading their schemas to check if they match the user's intent.
4. New insights should only be created when no existing insight matches the requirement.
</reasoning>
</example>
