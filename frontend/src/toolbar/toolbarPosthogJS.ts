import posthog from 'posthog-js'
import { useEffect, useState } from 'react'

import { FeatureFlagKey } from 'lib/constants'

const runningOnPosthog = !!window.POSTHOG_APP_CONTEXT
// Only the PostHog app knows the operator's collector. On a customer's site there is no key, so the toolbar sends nothing.
const apiKey = runningOnPosthog ? window.JS_POSTHOG_API_KEY : undefined

export const toolbarTelemetryEnabled = !!apiKey

const initResult = posthog.init(
    apiKey || 'fake_token',
    {
        // Without a key nothing is sent, so the host is never contacted. The page origin avoids naming any PostHog Cloud host.
        api_host: (toolbarTelemetryEnabled ? window.JS_POSTHOG_HOST : undefined) || window.location.origin,
        opt_out_capturing_by_default: true, // must call .opt_in_capturing() before any events are sent
        // Without a key the placeholder token would otherwise trigger remote config and flag requests.
        advanced_disable_flags: !toolbarTelemetryEnabled,
        persistence: 'memory', // We don't want to persist anything, all events are in-memory
        persistence_name: (apiKey || 'no_key') + '_toolbar', // We don't need this but it ensures we don't accidentally mess with the standard persistence
        bootstrap: {
            featureFlags: {},
        },
        // The web app imports toolbar modules, which creates this instance on every app page load.
        // Only a mounted toolbar reads these flags, so the toolbar loads them and starts the refresh when it mounts.
        advanced_disable_feature_flags_on_first_load: true,
        remote_config_refresh_interval_ms: 0,
        autocapture: false,
        // The toolbar runs on customer pages and must not install global exception handlers.
        capture_exceptions: false,
        capture_pageview: false,
        capture_pageleave: false,
        disable_surveys: true,
        disable_scroll_properties: true,
        disable_product_tours: true,
        disable_session_recording: true,
        session_recording: {
            // we want to capture the toolbar (which is marked with ph-no-capture
            // so customer sessions don't see it), but also respect the customer's
            // ph-no-capture marks
            blockClass: 'ph-internal-no-capture',
            blockSelector: '.ph-no-capture:not(#__POSTHOG_TOOLBAR__):not(#__POSTHOG_TOOLBAR__ *)',
            maskAllInputs: true,
        },
    },
    'ph_toolbar_internal'
)
if (!initResult) {
    throw new Error('Failed to initialize PostHog toolbar instance')
}
export const toolbarPosthogJS = initResult

if (runningOnPosthog && window.JS_POSTHOG_SELF_CAPTURE) {
    toolbarPosthogJS.debug()
}

/** Capture an exception with a required toolbar context tag for filtering. */
export function captureToolbarException(
    error: unknown,
    context: string,
    additionalProperties?: Record<string, unknown>
): void {
    toolbarPosthogJS.captureException(error, {
        toolbar_context: context,
        ...additionalProperties,
    })
}

export const useToolbarFeatureFlag = (flag: FeatureFlagKey, match?: string): boolean => {
    const [flagValue, setFlagValue] = useState<boolean | string | undefined>(toolbarPosthogJS.getFeatureFlag(flag))

    useEffect(() => {
        return toolbarPosthogJS.onFeatureFlags(() => setFlagValue(toolbarPosthogJS.getFeatureFlag(flag)))
    }, [flag, match])

    if (match) {
        return flagValue === match
    }

    return !!flagValue
}
