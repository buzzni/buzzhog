import { describe, expect, it } from 'vitest'
import { z } from 'zod'

import { ExperimentResultsGetSchema } from '@/schema/tool-inputs'
import { GENERATED_TOOLS as FEATURE_FLAG_TOOLS } from '@/tools/generated/feature_flags'

// Production traces show the dominant validation failure on the experiment tools is the
// experiment id arriving as `experimentId` / `experiment_id` where the schema requires
// `id` (the same mismatch the insight and flag tools already absorb). Every alias must
// normalize to `id` on every tool that takes an experiment id, or those failures come back.
/** Tool names whose advertised input schema has a top-level `id` property. */
function toolsWithIdParam(tools: Record<string, () => { schema: z.ZodTypeAny }>): string[] {
    return Object.entries(tools)
        .filter(([, factory]) => {
            const json = z.toJSONSchema(factory().schema, { io: 'input', reused: 'inline' }) as {
                properties?: Record<string, unknown>
            }
            return Boolean(json.properties?.id)
        })
        .map(([name]) => name)
        .sort()
}

describe('experiment id aliases', () => {
    const ALIAS_KEYS = ['experimentId', 'experiment_id'] as const

    describe('experiment-results-get (hand-written) normalizes aliases to `id`', () => {
        it.each([
            ['id (numeric)', { id: 123 }, 123],
            ['id (numeric string)', { id: '123' }, 123],
            ['experimentId', { experimentId: 123 }, 123],
            ['experiment_id', { experiment_id: '123' }, 123],
            ['id over aliases on conflict', { id: 1, experimentId: 2 }, 1],
        ])('accepts %s', (_label, input, expected) => {
            const result = ExperimentResultsGetSchema.safeParse(input)
            expect(result.success, JSON.stringify(result.error?.issues)).toBe(true)
            expect(result.data?.id).toBe(expected)
            expect(result.data?.refresh).toBe(false)
            for (const alias of ALIAS_KEYS) {
                expect(result.data).not.toHaveProperty(alias)
            }
        })

        it('still rejects a call with no identifier', () => {
            expect(ExperimentResultsGetSchema.safeParse({}).success).toBe(false)
        })
    })
})

// The flag tools only gained aliases on the by-key lookup; the id-based tools kept failing on
// `flagId` / `flag_id` at the same rate, so they take the numeric-id aliases too.
describe('feature flag id aliases', () => {
    const FLAG_ID_TOOLS = [
        'delete-feature-flag',
        'feature-flag-archive',
        'feature-flag-disable',
        'feature-flag-enable',
        'feature-flag-get-definition',
        'feature-flag-roll-out-to-everyone',
        'feature-flag-set-release-condition-rollout',
        'feature-flag-unarchive',
        'feature-flags-activity-retrieve',
        'feature-flags-dependent-flags-retrieve',
        'feature-flags-status-retrieve',
        'feature-flags-test-evaluation-create',
        'update-feature-flag',
    ] as const

    const ALIAS_KEYS = ['flagId', 'flag_id', 'feature_flag_id', 'featureFlagId'] as const

    const REQUIRED_EXTRAS: Record<string, Record<string, unknown>> = {
        'feature-flags-test-evaluation-create': { distinct_id: 'user-1' },
        'feature-flag-roll-out-to-everyone': { version: 3 },
        'feature-flag-set-release-condition-rollout': { condition_index: 0, rollout_percentage: 25, version: 3 },
    }

    // `id` on these is a scheduled change id, not a flag id.
    const NON_FLAG_ID_TOOLS = new Set(['scheduled-changes-delete', 'scheduled-changes-get', 'scheduled-changes-update'])

    it('covers every generated flag tool that takes a flag id', () => {
        const idTools = toolsWithIdParam(FEATURE_FLAG_TOOLS).filter((name) => !NON_FLAG_ID_TOOLS.has(name))
        expect(idTools).toEqual([...FLAG_ID_TOOLS].sort())
    })

    describe.each(FLAG_ID_TOOLS.map((name) => [name]))('%s normalizes aliases to `id`', (toolName) => {
        const factory = FEATURE_FLAG_TOOLS[toolName]
        const extras = REQUIRED_EXTRAS[toolName] ?? {}

        it.each([
            ['id (numeric)', { id: 7 }, 7],
            ['flagId', { flagId: 7 }, 7],
            ['flag_id', { flag_id: '7' }, 7],
            ['feature_flag_id', { feature_flag_id: 7 }, 7],
            ['featureFlagId', { featureFlagId: 7 }, 7],
            ['id over aliases on conflict', { id: 1, flagId: 2 }, 1],
        ])('accepts %s', (_label, input, expected) => {
            const result = factory!().schema.safeParse({ ...extras, ...input })
            expect(result.success, JSON.stringify(result.error?.issues)).toBe(true)
            const data = result.data as Record<string, unknown>
            expect(data.id).toEqual(expected)
            for (const alias of ALIAS_KEYS) {
                expect(data).not.toHaveProperty(alias)
            }
        })

        it('still rejects a call with no identifier', () => {
            expect(factory!().schema.safeParse({ ...extras }).success).toBe(false)
        })
    })
})
