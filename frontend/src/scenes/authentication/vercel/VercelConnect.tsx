import { LemonButton } from '@posthog/lemon-ui'

import { BridgePage } from 'lib/components/BridgePage/BridgePage'
import { SceneExport } from 'scenes/sceneTypes'

export const scene: SceneExport = {
    component: VercelConnect,
}

// This build serves no /api/vercel/connect routes, so the page can only say that linking is unavailable.
export function VercelConnect(): JSX.Element {
    return (
        <BridgePage view="vercel-connect">
            <h2 className="text-center">Vercel linking isn't available</h2>
            <p className="text-center mb-6">
                This version of PostHog can't link a Vercel account. Close this window and return to Vercel.
            </p>
            <LemonButton fullWidth type="secondary" center onClick={() => window.close()}>
                Close
            </LemonButton>
        </BridgePage>
    )
}
