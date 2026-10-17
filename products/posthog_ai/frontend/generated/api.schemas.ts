/**
 * Auto-generated from the Django backend OpenAPI schema.
 * To modify these types, update the Django serializers or views, then run:
 *   hogli build:openapi
 * Questions or issues? #team-devex on Slack
 *
 * PostHog API - generated
 * OpenAPI spec version: 1.0.0
 */
export interface JsonValueApi {}

/**
 * Agent instructions.
 */
export type TerminalAIRequestApiSystem = string | { [key: string]: JsonValueApi }[] | null

export type TerminalAIModelApi = (typeof TerminalAIModelApi)[keyof typeof TerminalAIModelApi]

export const TerminalAIModelApi = {
    ClaudeOpus5: 'claude-opus-5',
    ClaudeSonnet5: 'claude-sonnet-5',
    ClaudeSonnet46: 'claude-sonnet-4-6',
    ClaudeHaiku45: 'claude-haiku-4-5',
} as const

export type TerminalAIMessageRoleEnumApi =
    (typeof TerminalAIMessageRoleEnumApi)[keyof typeof TerminalAIMessageRoleEnumApi]

export const TerminalAIMessageRoleEnumApi = {
    User: 'user',
    Assistant: 'assistant',
} as const

/**
 * Anthropic text, image, or tool content blocks.
 */
export type TerminalAIMessageApiContent = string | { [key: string]: JsonValueApi }[]

export interface TerminalAIMessageApi {
    /** Author of this conversation message. */
    role: TerminalAIMessageRoleEnumApi
    /** Anthropic text, image, or tool content blocks. */
    content: TerminalAIMessageApiContent
}

/**
 * JSON schema for the tool's arguments.
 */
export type TerminalAIToolApiInputSchema = { [key: string]: JsonValueApi }

/**
 * Provider prompt cache settings.
 */
export type TerminalAIToolApiCacheControl = { [key: string]: string } | null

export interface TerminalAIToolApi {
    /**
     * Name of a tool executed inside the terminal.
     * @maxLength 128
     */
    name: string
    /**
     * What the tool does.
     * @maxLength 20000
     */
    description?: string
    /** JSON schema for the tool's arguments. */
    input_schema: TerminalAIToolApiInputSchema
    /** Provider prompt cache settings. */
    cache_control?: TerminalAIToolApiCacheControl
    /** Stream tool arguments as they are generated. */
    eager_input_streaming?: boolean | null
}

export interface TerminalAIRequestApi {
    /** Model served by the PostHog provider. */
    model: TerminalAIModelApi
    /**
     * Conversation and tool results.
     * @minItems 1
     * @maxItems 1000
     */
    messages: TerminalAIMessageApi[]
    /**
     * Maximum output tokens for this generation.
     * @minimum 1
     * @maximum 8192
     */
    max_tokens: number
    /** Always stream the model response. */
    stream?: true
    /** Agent instructions. */
    system?: TerminalAIRequestApiSystem
    /**
     * Tools executed by pi.
     * @maxItems 100
     */
    tools?: TerminalAIToolApi[]
    /** Sampling temperature. */
    temperature?: number | null
}

/**
 * * `dismissed` - Dismissed
 * * `accepted` - Accepted
 */
export type TurnSuggestionResolutionEnumApi =
    (typeof TurnSuggestionResolutionEnumApi)[keyof typeof TurnSuggestionResolutionEnumApi]

export const TurnSuggestionResolutionEnumApi = {
    Dismissed: 'dismissed',
    Accepted: 'accepted',
} as const

export interface ResolveTurnSuggestionApi {
    /** ID of the PostHog AI conversation (task) the suggestion card belongs to. */
    task_id: string
    /**
     * Zero-based index of the conversation turn the suggestion card was shown under.
     * @minimum 0
     */
    turn_index: number
    /** What the user did with the card: `dismissed` mutes suggestions for the rest of the conversation, `accepted` means the offered scout, notebook, alert or subscription was created.
     *
     * * `dismissed` - Dismissed
     * * `accepted` - Accepted */
    resolution: TurnSuggestionResolutionEnumApi
}

export interface ResolveTurnSuggestionResponseApi {
    /** Whether a suggestion card existed for that turn and this call recorded its outcome. A card keeps the first outcome recorded for it. */
    recorded: boolean
}

export interface TurnSuggestionStateApi {
    /** Whether the user dismissed a suggestion card in this conversation, which stops further cards. */
    muted: boolean
    /**
     * Zero-based indexes of the turns whose suggestion card the user already dismissed or accepted.
     * @items.minimum 0
     */
    resolved_turns: number[]
}

export type TerminalAiCreateParams = {
    format?: TerminalAiCreateFormat
}

export type TerminalAiCreateFormat = (typeof TerminalAiCreateFormat)[keyof typeof TerminalAiCreateFormat]

export const TerminalAiCreateFormat = {
    Json: 'json',
    Txt: 'txt',
} as const

export type TurnSuggestionsStateRetrieveParams = {
    /**
     * ID of the PostHog AI conversation (task) to read suggestion outcomes for.
     */
    task_id: string
}
