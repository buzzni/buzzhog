/**
 * Auto-generated Zod validation schemas from the Django backend OpenAPI schema.
 * To modify these schemas, update the Django serializers or views, then run:
 *   hogli build:openapi
 * Questions or issues? #team-devex on Slack
 *
 * PostHog API - generated
 * OpenAPI spec version: 1.0.0
 */
import * as zod from 'zod'

/**
 * Stream a terminal model response through PostHog AI. Requires organization approval for AI data processing. SDK consumers must use getTerminalAiCreateUrl() with streaming fetch. The generated JSON client buffers the response and cannot parse SSE.
 */
export const terminalAiCreateBodyMessagesMax = 1000

export const terminalAiCreateBodyMaxTokensMax = 8192

export const terminalAiCreateBodyStreamDefault = true
export const terminalAiCreateBodyToolsItemNameMax = 128

export const terminalAiCreateBodyToolsItemDescriptionDefault = ``
export const terminalAiCreateBodyToolsItemDescriptionMax = 20000

export const terminalAiCreateBodyToolsMax = 100

export const terminalAiCreateBodyTemperatureOneMin = 0
export const terminalAiCreateBodyTemperatureOneMax = 1

export const TerminalAiCreateBody = /* @__PURE__ */ zod.object({
    model: zod
        .enum(['claude-opus-5', 'claude-sonnet-5', 'claude-sonnet-4-6', 'claude-haiku-4-5'])
        .describe('Model served by the PostHog provider.'),
    messages: zod
        .array(
            zod.object({
                role: zod.enum(['user', 'assistant']).describe('Author of this conversation message.'),
                content: zod
                    .union([zod.string(), zod.array(zod.record(zod.string(), zod.unknown()))])
                    .describe('Anthropic text, image, or tool content blocks.'),
            })
        )
        .min(1)
        .max(terminalAiCreateBodyMessagesMax)
        .describe('Conversation and tool results.'),
    max_tokens: zod
        .number()
        .min(1)
        .max(terminalAiCreateBodyMaxTokensMax)
        .describe('Maximum output tokens for this generation.'),
    stream: zod.boolean().default(terminalAiCreateBodyStreamDefault).describe('Always stream the model response.'),
    system: zod
        .union([zod.string(), zod.array(zod.record(zod.string(), zod.unknown())), zod.null()])
        .optional()
        .describe('Agent instructions.'),
    tools: zod
        .array(
            zod.object({
                name: zod
                    .string()
                    .max(terminalAiCreateBodyToolsItemNameMax)
                    .describe('Name of a tool executed inside the terminal.'),
                description: zod
                    .string()
                    .max(terminalAiCreateBodyToolsItemDescriptionMax)
                    .default(terminalAiCreateBodyToolsItemDescriptionDefault)
                    .describe('What the tool does.'),
                input_schema: zod.record(zod.string(), zod.unknown()).describe("JSON schema for the tool's arguments."),
                cache_control: zod
                    .union([zod.record(zod.string(), zod.string()), zod.null()])
                    .optional()
                    .describe('Provider prompt cache settings.'),
                eager_input_streaming: zod
                    .union([zod.boolean(), zod.null()])
                    .optional()
                    .describe('Stream tool arguments as they are generated.'),
            })
        )
        .max(terminalAiCreateBodyToolsMax)
        .optional()
        .describe('Tools executed by pi.'),
    temperature: zod
        .union([
            zod.number().min(terminalAiCreateBodyTemperatureOneMin).max(terminalAiCreateBodyTemperatureOneMax),
            zod.null(),
        ])
        .optional()
        .describe('Sampling temperature.'),
})

/**
 * @summary Record what the user did with a PostHog AI turn suggestion card
 */
export const turnSuggestionsResolveCreateBodyTurnIndexMin = 0

export const TurnSuggestionsResolveCreateBody = /* @__PURE__ */ zod.object({
    task_id: zod.uuid().describe('ID of the PostHog AI conversation (task) the suggestion card belongs to.'),
    turn_index: zod
        .number()
        .min(turnSuggestionsResolveCreateBodyTurnIndexMin)
        .describe('Zero-based index of the conversation turn the suggestion card was shown under.'),
    resolution: zod
        .enum(['dismissed', 'accepted'])
        .describe('\* `dismissed` - Dismissed\n\* `accepted` - Accepted')
        .describe(
            'What the user did with the card: `dismissed` mutes suggestions for the rest of the conversation, `accepted` means the offered scout, notebook, alert or subscription was created.\n\n\* `dismissed` - Dismissed\n\* `accepted` - Accepted'
        ),
})
