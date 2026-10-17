import { useActions } from 'kea'

import { IconTrash } from '@posthog/icons'
import { LemonButton } from '@posthog/lemon-ui'

import { RestrictionScope, useRestrictedArea } from 'lib/components/RestrictedArea'
import { OrganizationMembershipLevel } from 'lib/constants'
import { IconOpenInNew } from 'lib/lemon-ui/icons'
import { organizationIntegrationsLogic } from 'scenes/settings/organization/organizationIntegrationsLogic'

import { IntegrationType } from '~/types'

function DisconnectButton({ integration }: { integration: IntegrationType }): JSX.Element {
    const { deleteOrganizationIntegration } = useActions(organizationIntegrationsLogic)
    const restrictedReason = useRestrictedArea({
        scope: RestrictionScope.Organization,
        minimumAccessLevel: OrganizationMembershipLevel.Admin,
    })

    return (
        <LemonButton
            type="secondary"
            status="danger"
            onClick={() => deleteOrganizationIntegration(integration.id)}
            icon={<IconTrash />}
            disabledReason={restrictedReason}
        >
            Disconnect
        </LemonButton>
    )
}

export function VercelIntegrationSuffix({ integration }: { integration: IntegrationType }): JSX.Element {
    const accountUrl = integration.config?.account?.url
    const accountName = integration.config?.account?.name
    const isConnectable = integration.config?.type === 'connectable'

    if (!isConnectable) {
        return (
            <div className="flex gap-2">
                {accountUrl && (
                    <LemonButton
                        type="secondary"
                        to={accountUrl}
                        targetBlank
                        sideIcon={<IconOpenInNew />}
                        tooltip={accountName ? `Open ${accountName} in Vercel` : 'Open in Vercel'}
                    >
                        View in Vercel
                    </LemonButton>
                )}
                <DisconnectButton integration={integration} />
            </div>
        )
    }

    return (
        <div className="flex justify-end">
            <DisconnectButton integration={integration} />
        </div>
    )
}
