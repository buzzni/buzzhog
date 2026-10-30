import { LemonDialog } from '@posthog/lemon-ui'

export const DELETE_CHAT_UNAVAILABLE = "Deleting chats isn't available in this version."

export function openDeleteConversationDialog(onConfirm: () => void): void {
    LemonDialog.open({
        title: 'Delete chat?',
        description: 'The chat will be removed from your history.',
        primaryButton: {
            children: 'Delete',
            status: 'danger',
            onClick: onConfirm,
        },
        secondaryButton: { children: 'Cancel' },
    })
}
