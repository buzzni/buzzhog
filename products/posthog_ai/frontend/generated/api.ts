import { apiMutator } from '../../../../frontend/src/lib/api-orval-mutator'
/**
 * Auto-generated from the Django backend OpenAPI schema.
 * To modify these types, update the Django serializers or views, then run:
 *   hogli build:openapi
 * Questions or issues? #team-devex on Slack
 *
 * PostHog API - generated
 * OpenAPI spec version: 1.0.0
 */
import type {
    ResolveTurnSuggestionApi,
    ResolveTurnSuggestionResponseApi,
    TerminalAIRequestApi,
    TerminalAiCreateParams,
    TurnSuggestionStateApi,
    TurnSuggestionsStateRetrieveParams,
} from './api.schemas'

export const getTerminalAiCreateUrl = (projectId: string, params?: TerminalAiCreateParams) => {
    const normalizedParams = new URLSearchParams()

    Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined) {
            normalizedParams.append(key, value === null ? 'null' : String(value))
        }
    })

    const stringifiedParams = normalizedParams.toString()

    return stringifiedParams.length > 0
        ? `/api/projects/${projectId}/terminal_ai/?${stringifiedParams}`
        : `/api/projects/${projectId}/terminal_ai/`
}

/**
 * Stream a terminal model response through PostHog AI. Requires organization approval for AI data processing. SDK consumers must use getTerminalAiCreateUrl() with streaming fetch. The generated JSON client buffers the response and cannot parse SSE.
 */
export const terminalAiCreate = async (
    projectId: string,
    terminalAIRequestApi: TerminalAIRequestApi,
    params?: TerminalAiCreateParams,
    options?: RequestInit
): Promise<string> => {
    return apiMutator<string>(getTerminalAiCreateUrl(projectId, params), {
        ...options,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        body: JSON.stringify(terminalAIRequestApi),
    })
}

export const getTurnSuggestionsResolveCreateUrl = (projectId: string) => {
    return `/api/projects/${projectId}/turn_suggestions/resolve/`
}

/**
 * @summary Record what the user did with a PostHog AI turn suggestion card
 */
export const turnSuggestionsResolveCreate = async (
    projectId: string,
    resolveTurnSuggestionApi: ResolveTurnSuggestionApi,
    options?: RequestInit
): Promise<ResolveTurnSuggestionResponseApi> => {
    return apiMutator<ResolveTurnSuggestionResponseApi>(getTurnSuggestionsResolveCreateUrl(projectId), {
        ...options,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        body: JSON.stringify(resolveTurnSuggestionApi),
    })
}

export const getTurnSuggestionsStateRetrieveUrl = (projectId: string, params: TurnSuggestionsStateRetrieveParams) => {
    const normalizedParams = new URLSearchParams()

    Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined) {
            normalizedParams.append(key, value === null ? 'null' : String(value))
        }
    })

    const stringifiedParams = normalizedParams.toString()

    return stringifiedParams.length > 0
        ? `/api/projects/${projectId}/turn_suggestions/state/?${stringifiedParams}`
        : `/api/projects/${projectId}/turn_suggestions/state/`
}

/**
 * @summary Read which PostHog AI turn suggestion cards the user already resolved
 */
export const turnSuggestionsStateRetrieve = async (
    projectId: string,
    params: TurnSuggestionsStateRetrieveParams,
    options?: RequestInit
): Promise<TurnSuggestionStateApi> => {
    return apiMutator<TurnSuggestionStateApi>(getTurnSuggestionsStateRetrieveUrl(projectId, params), {
        ...options,
        method: 'GET',
    })
}
