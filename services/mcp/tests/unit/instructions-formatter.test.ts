import { describe, expect, it } from 'vitest'

import { MCP_INSTRUCTIONS_CHAR_BUDGET } from '@/lib/constants'
import { buildToolDomainsCompact, type QueryToolInfo } from '@/lib/instructions'
import { InstructionsFormatter, type InstructionsContext } from '@/lib/instructions-formatter'

// `tools` mirrors production: the full tool set, query-* included (the domain
// extractor collapses them into the single `query` domain). `queryTools` below
// is the parallel catalog projection with hints.
const realisticTools = [
    { name: 'dashboard-create', category: 'Dashboards' },
    { name: 'dashboard-get', category: 'Dashboards' },
    { name: 'feature-flag-create', category: 'Feature flags' },
    { name: 'feature-flag-get-all', category: 'Feature flags' },
    { name: 'cohorts-list', category: 'Cohorts' },
    { name: 'project-get', category: 'Core' },
    { name: 'business-knowledge-documents-search', category: 'Business knowledge' },
    { name: 'query-trends', category: 'Query wrappers' },
    { name: 'query-funnel', category: 'Query wrappers' },
]
const realisticQueryTools: QueryToolInfo[] = [
    { name: 'query-trends', title: 'Trends', systemPromptHint: 'time series' },
    { name: 'query-funnel', title: 'Funnel', systemPromptHint: 'conversion rate' },
]
const ENV_POINTER = 'Call `project-get` without an ID to read the active project'

const fullCtx: InstructionsContext = {
    guidelines: 'some guidelines',
    tools: realisticTools,
    queryTools: realisticQueryTools,
    renderUiEnabled: true,
}

describe('InstructionsFormatter', () => {
    describe('buildToolsInstructions', () => {
        it('resolves every placeholder when fully populated', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions(fullCtx)
            expect(result).toContain(ENV_POINTER)
            expect(result).toContain('- dashboard')
            expect(result).toContain('- feature-flag')
            expect(result).toContain('- `query-funnel` — conversion rate')
            expect(result).toContain('- `query-trends` — time series')
            expect(result).not.toMatch(/\{tool_domains\}|\{query_tools\}|\{guidelines\}/)
        })

        it('renders the basic functionality, retrieving data, and examples sections', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions(fullCtx)
            expect(result).toContain('### Basic functionality')
            expect(result).toContain('### Business knowledge')
            expect(result).toContain('`business-knowledge-documents-search`')
            expect(result).toContain('### Retrieving data')
            expect(result).toContain('### Examples')
        })

        it('does not leak any CLI-only sections (tools mode is not exec mode)', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions(fullCtx)
            expect(result).not.toContain('SCHEMA DRILL-DOWN RULE')
            expect(result).not.toContain('Using the `posthog` tool')
            expect(result).not.toContain('CLI-style command string')
        })

        it('omits placeholders cleanly when context fields are undefined', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions({ guidelines: 'rules' })
            expect(result).not.toContain('{guidelines}')
            expect(result).not.toContain('{tool_domains}')
            expect(result).not.toContain('{query_tools}')
        })

        it('omits business knowledge guidance when search is unavailable', () => {
            const formatter = new InstructionsFormatter()
            expect(formatter.buildToolsInstructions({ guidelines: 'rules' })).not.toContain('### Business knowledge')
        })

        it('includes business knowledge guidance when document search is available', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions({
                guidelines: 'rules',
                tools: [{ name: 'business-knowledge-documents-search', category: 'Business knowledge' }],
            })

            expect(result).toContain('### Business knowledge')
            expect(result).toContain('`business-knowledge-documents-search`')
            expect(result).not.toContain('docs-search')
        })

        it('always includes the agent-feedback section', () => {
            const formatter = new InstructionsFormatter()
            expect(formatter.buildToolsInstructions(fullCtx)).toContain('### Sharing feedback on PostHog')
            expect(formatter.buildToolsInstructions({ guidelines: 'rules' })).toContain(
                '### Sharing feedback on PostHog'
            )
        })
    })

    describe('buildExecInstructions', () => {
        it('renders the compact instructions section with placeholders resolved', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecInstructions(fullCtx)
            // query-* tools surface as the single `query` domain, not a separate catalog line
            expect(result).toContain('business-knowledge-documents|cohorts|dashboard|feature-flag|project|query')
            expect(result).not.toContain('### Business knowledge')
            expect(result).not.toContain('query-*:')
            // Env context is not here — it rides the exec command description, which has no
            // truncation cap, leaving this payload's whole budget to the domain index.
            expect(result).not.toContain(ENV_POINTER)
            expect(result).not.toMatch(/\{tool_domains\}|\{query_tools\}|\{guidelines\}/)
        })

        // Synthetic fixture: 60 uniform `domain-N-get` names collapse to short domains and
        // cost ~1/3 of what the live catalog does, which is how a 2,923-char payload shipped
        // past a passing 2048 assertion. Kept for the placeholder wiring it exercises; the
        // assertion that actually guards the cap runs the real catalog, in
        // `instructions-formatter-snapshot.test.ts`.
        it('stays under the character budget at synthetic tool counts', () => {
            const manyTools = Array.from({ length: 60 }, (_, i) => ({
                name: `domain-${i}-get`,
                category: `Category ${i % 6}`,
            }))
            const manyQueryTools: QueryToolInfo[] = Array.from({ length: 12 }, (_, i) => ({
                name: `query-tool-${i}`,
                title: `Query tool ${i}`,
                systemPromptHint: `short hint for query tool ${i}`,
            }))
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecInstructions({
                guidelines: 'guidelines',
                tools: manyTools,
                queryTools: manyQueryTools,
            })
            expect(result.length).toBeLessThanOrEqual(MCP_INSTRUCTIONS_CHAR_BUDGET)
        })

        // The domain index names PostHog resources, not callable tools, so without this
        // line the payload never states what can actually be called. `render-ui` is only
        // mounted on MCP Apps hosts — naming it elsewhere advertises a tool that isn't there.
        it('names the callable tools, gating render-ui on the host mounting it', () => {
            const formatter = new InstructionsFormatter()
            const withUi = formatter.buildExecInstructions({ ...fullCtx, renderUiEnabled: true })
            const withoutUi = formatter.buildExecInstructions({ ...fullCtx, renderUiEnabled: false })

            expect(withUi).toContain('exec – run any PostHog command')
            expect(withUi).toContain('render-ui – show a tool result as an interactive app.')
            expect(withoutUi).toContain('exec – run any PostHog command')
            expect(withoutUi).not.toContain('render-ui')
        })

        it('does not bleed the full command reference into the compact instructions', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecInstructions(fullCtx)
            expect(result).not.toContain('SCHEMA DRILL-DOWN RULE')
            expect(result).not.toContain('### Basic functionality')
            expect(result).not.toContain('### Examples')
        })
    })

    describe('buildExecToolDescription', () => {
        it('renders just the exec tool blurb, no other sections', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecToolDescription()
            expect(result).toContain('Using the `posthog` tool')
            expect(result).toContain('Run `info <tool_name>` once if its schema is not in context.')
            expect(result).not.toContain('### Basic functionality')
            expect(result).not.toContain('### Examples')
            expect(result).not.toContain('### Business knowledge')
        })

        it('leads with business knowledge guidance when document search is available', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecToolDescription({ businessKnowledgeSearchEnabled: true })

            expect(result).toContain('### Business knowledge')
            expect(result.indexOf('### Business knowledge')).toBeLessThan(result.indexOf('Using the `posthog` tool'))
            // The mandate leads the description, ahead of the grammar it depends on.
            expect(result).toContain('`call business-knowledge-documents-search <json_input>`')
        })

        it('omits knowledge guidance when document search is unavailable', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecToolDescription({ businessKnowledgeRepoSearchEnabled: true })

            expect(result).not.toContain('### Business knowledge')
        })

        it('loads skills before checking business knowledge and repositories', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecToolDescription({
                skillsEnabled: true,
                businessKnowledgeSearchEnabled: true,
                businessKnowledgeRepoSearchEnabled: true,
                businessKnowledgeWindowEnabled: true,
            })

            expect(result.indexOf('SKILLS FIRST')).toBeGreaterThanOrEqual(0)
            expect(result.indexOf('SKILLS FIRST')).toBeLessThan(result.indexOf('### Business knowledge'))
            expect(result.indexOf('business-knowledge-documents-search')).toBeLessThan(
                result.indexOf('`call business-knowledge-repositories-search <json_input>`')
            )
            expect(result).toContain('Code or doc misses')
            expect(result.length).toBeLessThanOrEqual(2048)
        })
    })

    describe('repository search guidance', () => {
        it.each([
            { name: 'repo search without knowledge search', bk: false, repo: true, expected: false },
            { name: 'knowledge search without repo search', bk: true, repo: false, expected: false },
            { name: 'both', bk: true, repo: true, expected: true },
        ])('names repository search only when both tools are advertised: $name', ({ bk, repo, expected }) => {
            const tools = [
                ...(bk ? [{ name: 'business-knowledge-documents-search', category: 'Business knowledge' }] : []),
                ...(repo ? [{ name: 'business-knowledge-repositories-search', category: 'Business knowledge' }] : []),
            ]
            const result = new InstructionsFormatter().buildToolsInstructions({ ...fullCtx, tools })
            expect(result.includes('`business-knowledge-repositories-search`')).toBe(expected)
        })
    })

    describe('document window guidance', () => {
        it.each([
            { name: 'window tool advertised', window: true },
            { name: 'window tool withheld', window: false },
        ])('names the window tool only when it is advertised: $name', ({ window }) => {
            const tools = [
                { name: 'business-knowledge-documents-search', category: 'Business knowledge' },
                ...(window
                    ? [{ name: 'business-knowledge-document-window-retrieve', category: 'Business knowledge' }]
                    : []),
            ]
            const formatter = new InstructionsFormatter()
            const result = formatter.buildToolsInstructions({ ...fullCtx, tools })
            expect(result.includes('`business-knowledge-document-window-retrieve`')).toBe(window)
            // In exec mode a bare tool name reads as a command and is rejected, so the line must use `call`.
            const execResult = formatter.buildExecToolDescription({
                businessKnowledgeSearchEnabled: true,
                businessKnowledgeWindowEnabled: window,
            })
            expect(execResult.includes('`call business-knowledge-document-window-retrieve <json_input>`')).toBe(window)
        })
    })

    describe('buildExecCommandReference', () => {
        it.each([
            { name: 'project-get', tools: ['project-get'], project: true },
            { name: 'no lookup tool', tools: [], project: false },
        ])('names only the env lookup tools the roster has: $name', ({ tools, project }) => {
            const ctx = { ...fullCtx, tools: tools.map((name) => ({ name, category: 'Core' })) }
            const result = new InstructionsFormatter().buildExecCommandReference(ctx)
            expect(result.includes(ENV_POINTER)).toBe(project)
            expect(result.includes('### Active environment')).toBe(project)
        })

        it('carries the CLI mechanics', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecCommandReference(fullCtx)
            expect(result).toContain('SCHEMA DRILL-DOWN RULE')
            expect(result).not.toContain('### Business knowledge')
            expect(result).toContain('### Basic functionality')
            expect(result).toContain('### Examples')
        })

        it('does not include the exec-tool blurb (that lives on the tool description)', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecCommandReference(fullCtx)
            expect(result).not.toContain('Using the `posthog` tool')
        })

        it('embeds the env-context pointer and query-tool catalog', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildExecCommandReference(fullCtx)
            expect(result).toContain(ENV_POINTER)
            // Tool domains are temporarily omitted from the command reference while
            // probing claude.ai's per-tool size cap; discovery rides on `search`.
            expect(result).not.toContain('cohorts|dashboard')
            expect(result).toContain('- `query-trends` — time series')
        })

        it('always includes the agent-feedback section', () => {
            const formatter = new InstructionsFormatter()
            const withFeedback = formatter.buildExecCommandReference(fullCtx)
            expect(withFeedback).toContain('### Sharing feedback on PostHog')
        })

        it('includes the rendering section only when render-ui is available for the client', () => {
            const formatter = new InstructionsFormatter()
            const withRendering = formatter.buildExecCommandReference(fullCtx)
            expect(withRendering).toContain('### Rendering visualizations')

            // The raw flag being on isn't enough — a non-UI-host client (e.g. Claude Code)
            // resolves `renderUiEnabled` to false and must not see the rendering section.
            const withoutRendering = formatter.buildExecCommandReference({ ...fullCtx, renderUiEnabled: false })
            expect(withoutRendering).not.toContain('### Rendering visualizations')
        })
    })

    describe('Claude web/desktop exec guidance', () => {
        it('keeps routine guidance inline and advertises optional topics', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildClaudeExecCommandReference(fullCtx)

            // Skills off is the shipped default: the reference must carry no skill syntax.
            expect(result).not.toContain('(posthog|project):<skill>')
            expect(result).not.toContain('SKILLS FIRST')

            expect(result).toContain('**LEARN FIRST: HARD REQUIREMENT**')
            expect(result).toContain('learn <topic...> - load one or more learning topics')
            expect(result).toContain('Topics are cumulative.')
            expect(result).toContain('User: create pageviews visualization')
            expect(result).toContain(
                "Assistant: This needs analytics and visualization guidance, so I'll load both first."
            )
            expect(result).toContain('posthog:exec({"command":"learn analytics visualizations"})')
            expect(result).toContain('User: How many weekly active users do we have?')
            expect(result).toContain('render-ui({ "tool_name": "query-trends", "tool_input": {...} })')
            expect(result.indexOf('render-ui({ "tool_name": "query-trends"')).toBeGreaterThan(
                result.indexOf('posthog:exec({"command":"call query-trends {...}"})')
            )
            expect(result).toContain('- analytics:')
            expect(result).toContain('- visualizations:')
            expect(result).toContain('- urls:')
            expect(result).toContain('- feedback:')
            expect(result).toContain('SCHEMA DRILL-DOWN RULE')
            expect(result).toContain('**CORRECT usage pattern:**')
            expect(result.indexOf('User: create pageviews visualization')).toBeGreaterThan(
                result.indexOf('**CORRECT usage pattern:**')
            )
            expect(result).toContain('### Basic functionality')
            expect(result).toContain('### Tool search')
            expect(result).toContain(buildToolDomainsCompact(realisticTools))
            expect(result).toContain(ENV_POINTER)
            expect(result).not.toContain('### Retrieving data')
            expect(result).not.toContain('### Examples')
            expect(result).not.toContain('### Rendering visualizations')
            expect(result).not.toContain('### URL patterns')
            expect(result).not.toContain('### Sharing feedback on PostHog')
            expect(result).not.toContain('- `query-trends` — time series')
            expect(result).not.toMatch(/\{help_topics\}|\{query_tools\}|\{guidelines\}/)
        })

        it('advertises skill syntax inside the schema budget only when skills are enabled', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildClaudeExecCommandReference(fullCtx, { skillsEnabled: true })

            expect(result).toContain('**SKILLS FIRST: HARD REQUIREMENT**')
            expect(result).toContain('(posthog|project):<skill> [path...]')
            // The compact variant, not the full routing paragraph, which belongs to the uncapped reference.
            expect(result).not.toContain('never clone, grep, or web-search PostHog internals')
            expect(result).toContain('- analytics:')
            expect(result).toContain('learn <topic...> - load one or more learning topics')
        })

        it('keeps URL patterns inline when learn is unavailable', () => {
            const formatter = new InstructionsFormatter()
            const result = formatter.buildClaudeExecCommandReference(fullCtx, {
                learnEnabled: false,
                skillsEnabled: false,
            })

            expect(result).toContain('### URL patterns')
            expect(result).not.toContain('- urls:')
            expect(result).not.toContain('learn <topic...>')
        })

        it('adds the full skills-first routing to the uncapped reference only when enabled', () => {
            const formatter = new InstructionsFormatter()
            const off = formatter.buildExecCommandReference(fullCtx)
            const on = formatter.buildExecCommandReference(fullCtx, { learnEnabled: true })

            expect(off).not.toContain('SKILLS FIRST')
            expect(on).toContain('**SKILLS FIRST: HARD REQUIREMENT**')
            expect(on).toContain('never clone, grep, or web-search PostHog internals')
        })

        it('builds optional learning topics from their full guidance', () => {
            const formatter = new InstructionsFormatter()
            const entries = formatter.buildClaudeExecLearnGuides(fullCtx)
            const analytics = entries.find((entry) => entry.id === 'analytics')

            expect(entries.map(({ id }) => id)).toEqual(['analytics', 'visualizations', 'urls', 'feedback'])
            expect(analytics?.content).toContain('### Retrieving data')
            expect(analytics?.content).toContain('### Examples')
            expect(analytics?.content).toContain('- `query-trends` — time series')
            expect(entries.find((entry) => entry.id === 'visualizations')?.content).toContain(
                '### Rendering visualizations'
            )
            expect(entries.find((entry) => entry.id === 'urls')?.content).toContain('### URL patterns')
            expect(entries.find((entry) => entry.id === 'feedback')?.content).toContain(
                '### Sharing feedback on PostHog'
            )
        })

        it('only advertises visualizations when rendering is available', () => {
            const formatter = new InstructionsFormatter()
            const ctx = {
                ...fullCtx,
                renderUiEnabled: false,
            }

            expect(formatter.buildClaudeExecLearnGuides(ctx).map((entry) => entry.id)).toEqual([
                'analytics',
                'urls',
                'feedback',
            ])
            const result = formatter.buildClaudeExecCommandReference(ctx)
            expect(result).toContain('- analytics:')
            expect(result).not.toContain('- visualizations:')
            expect(result).toContain('- urls:')
            expect(result).toContain('- feedback:')
        })
    })

    // A blanket "search before every answer" mandate fired a business-knowledge search
    // on unrelated requests. The exec description reaches any client that lists tool
    // descriptions, so both surfaces carrying the section must scope it by topic.
    describe('knowledge-search scoping', () => {
        it.each([
            {
                name: 'buildToolsInstructions',
                render: (formatter: InstructionsFormatter) => formatter.buildToolsInstructions(fullCtx),
            },
            {
                name: 'buildExecToolDescription',
                render: (formatter: InstructionsFormatter) =>
                    formatter.buildExecToolDescription({ businessKnowledgeSearchEnabled: true }),
            },
        ])('$name only mandates a search for project and company questions', ({ render }) => {
            const result = render(new InstructionsFormatter())

            expect(result).toContain('### Business knowledge')
            expect(result).not.toMatch(/every user request|even when the request looks simple/)
            expect(result).toContain('call no search')
            // The gate is the topic, never the location: a project or company question that names a
            // file in the user's repository still has to reach business knowledge search.
            expect(result).toContain('The topic decides, not the location')
        })
    })

    describe('metric discovery gating (data catalog flag)', () => {
        const surfaces: {
            name: string
            render: (formatter: InstructionsFormatter, ctx: InstructionsContext) => string
            mustPrecede: string[]
        }[] = [
            {
                name: 'buildToolsInstructions',
                render: (formatter, ctx) => formatter.buildToolsInstructions(ctx),
                mustPrecede: ['### Retrieving data'],
            },
            {
                name: 'analytics learn topic content',
                render: (formatter, ctx) =>
                    formatter.buildClaudeExecLearnGuides(ctx).find((entry) => entry.id === 'analytics')!.content,
                mustPrecede: ['### Retrieving data'],
            },
            {
                name: 'buildExecCommandReference',
                render: (formatter, ctx) => formatter.buildExecCommandReference(ctx),
                mustPrecede: ['SCHEMA DRILL-DOWN RULE', '### Retrieving data'],
            },
        ]

        it.each(surfaces)('$name puts metric routing before generic analytics guidance', ({ render, mustPrecede }) => {
            const formatter = new InstructionsFormatter()
            const rendered = render(formatter, fullCtx)
            const metricRoutingPosition = rendered.indexOf('#### Metric discovery (semantic layer)')
            expect(metricRoutingPosition).toBeGreaterThanOrEqual(0)
            expect(rendered).toContain('metric-list')
            expect(rendered).toContain('metric-describe')
            expect(rendered).toContain('data-catalog-metric-run')
            for (const genericGuidance of mustPrecede) {
                expect(metricRoutingPosition).toBeLessThan(rendered.indexOf(genericGuidance))
            }
        })

        it('advertises governed metrics in the analytics topic description', () => {
            const formatter = new InstructionsFormatter()
            const analyticsEntry = formatter
                .buildClaudeExecLearnGuides(fullCtx)
                .find((entry) => entry.id === 'analytics')!
            expect(analyticsEntry.description).toContain('governed metrics')
        })
    })

    describe('analysis artifact guidance', () => {
        const surfaces: {
            name: string
            render: (formatter: InstructionsFormatter, ctx: InstructionsContext) => string
        }[] = [
            {
                name: 'buildToolsInstructions',
                render: (formatter, ctx) => formatter.buildToolsInstructions(ctx),
            },
            {
                name: 'analytics learn topic content',
                render: (formatter, ctx) =>
                    formatter.buildClaudeExecLearnGuides(ctx).find((entry) => entry.id === 'analytics')!.content,
            },
            {
                name: 'buildExecCommandReference',
                render: (formatter, ctx) => formatter.buildExecCommandReference(ctx),
            },
        ]

        it.each(surfaces)('$name routes deep dives to notebooks and tracking to dashboards', ({ render }) => {
            const formatter = new InstructionsFormatter()
            const result = render(formatter, fullCtx)
            expect(result).toContain('### Where an analysis lands')
            expect(result).toContain('**Notebook**')
            expect(result).toContain('**Dashboard**')
        })

        // The SQL and Python guidance names `notebooks-add-cell`, so it must stay out of prompts
        // for clients that aren't advertised the cell tools.
        it.each(surfaces)('$name gates the SQL and Python sections on the notebook cell tools', ({ render }) => {
            const formatter = new InstructionsFormatter()
            const cellsOn = render(formatter, { ...fullCtx, notebookCellsEnabled: true })
            expect(cellsOn).toContain('### SQL in an analysis')
            expect(cellsOn).toContain("cell_type: 'sql'")
            expect(cellsOn).toContain('### Python in an analysis')
            expect(cellsOn).toContain("cell_type: 'python'")

            const cellsOff = render(formatter, { ...fullCtx, notebookCellsEnabled: false })
            expect(cellsOff).not.toContain('### SQL in an analysis')
            expect(cellsOff).not.toContain('### Python in an analysis')
            expect(cellsOff).toBe(render(formatter, fullCtx))
        })
    })

    describe('activity history guidance', () => {
        const surfaces: {
            name: string
            render: (formatter: InstructionsFormatter, ctx: InstructionsContext) => string
            inline: boolean
        }[] = [
            { name: 'tools', render: (f, ctx) => f.buildToolsInstructions(ctx), inline: true },
            { name: 'exec', render: (f, ctx) => f.buildExecCommandReference(ctx), inline: true },
            {
                name: 'Claude analytics guide',
                render: (f, ctx) =>
                    f.buildClaudeExecLearnGuides(ctx).find((entry) => entry.id === 'analytics')!.content,
                inline: true,
            },
            {
                name: 'Claude without guides',
                render: (f, ctx) => f.buildClaudeExecCommandReference(ctx, { learnEnabled: false }),
                inline: true,
            },
            {
                name: 'Claude with guides',
                render: (f, ctx) => f.buildClaudeExecCommandReference(ctx),
                inline: false,
            },
        ]

        it.each(
            surfaces.flatMap((surface) =>
                [
                    { capability: 'neither reader', tools: [], history: false },
                    {
                        capability: 'activity reader only',
                        tools: ['advanced-activity-logs-list'],
                        history: true,
                    },
                ].map((capability) => ({ ...surface, ...capability }))
            )
        )('$name exposes only supported history procedures: $capability', ({ render, inline, tools, history }) => {
            const result = render(new InstructionsFormatter(), {
                ...fullCtx,
                tools: tools.map((name) => ({ name, category: 'Platform Features' })),
            })

            expect(result.includes('### Activity history')).toBe(inline && history)
            if (inline && history) {
                expect(result).toContain('`start_date`, `end_date`')
                expect(result).toContain('`page_size: 10`')
                expect(result).toContain('`clients: ["scout:<skill_name>"]`')
                expect(result).toContain('If access is denied, stop using this reader')
                expect(result).toContain('Other advertised, authorized history readers, including per-object readers')
            }
        })
    })

    // Mirrors the single-exec wiring in `src/mcp.ts`. When the client honors the MCP
    // `instructions` field, that payload carries exactly one thing — the tool-domain index
    // (including the `query` domain) — because clients hard-truncate it. Everything else,
    // env-context and the query-tool catalog included, stays on the `command` description,
    // which has no cap. Codex (no `instructions` support) keeps today's behavior: empty
    // `instructions`, everything inlined in the `command` description.
    describe('exec mode wiring', () => {
        it.each([
            { name: 'supportsInstructions=true (Claude Code etc.)', supportsInstructions: true },
            { name: 'supportsInstructions=false (Codex)', supportsInstructions: false },
        ])('$name: splits product context between instructions and commandReference', ({ supportsInstructions }) => {
            const formatter = new InstructionsFormatter()
            const instructions = supportsInstructions ? formatter.buildExecInstructions(fullCtx) : ''
            const commandReference = formatter.buildExecCommandReference(fullCtx)

            expect(commandReference).toContain('SCHEMA DRILL-DOWN RULE')
            expect(commandReference).toContain('### Basic functionality')
            // the query catalog always lives on the command reference, both modes
            expect(commandReference).toContain('- `query-trends` — time series')

            if (supportsInstructions) {
                // queries surface in instructions only as the `query` tool domain
                expect(instructions).toContain(
                    'business-knowledge-documents|cohorts|dashboard|feature-flag|project|query'
                )
                expect(instructions).not.toContain('- `query-trends` — time series')
                expect(instructions).not.toContain(ENV_POINTER)
                expect(commandReference).toContain(ENV_POINTER)
                expect(commandReference).not.toContain('cohorts|dashboard')
            } else {
                expect(instructions).toBe('')
                expect(commandReference).toContain('- `query-trends` — time series')
                expect(commandReference).toContain(ENV_POINTER)
                expect(commandReference).not.toContain('cohorts|dashboard')
            }
        })
    })
})
