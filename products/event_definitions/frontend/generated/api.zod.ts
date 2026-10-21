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

export const eventDefinitionsCreateBodyNameMax = 400

export const eventDefinitionsCreateBodyPrimaryPropertyMax = 400

export const eventDefinitionsCreateBodyPostToSlackDefault = false

export const EventDefinitionsCreateBody = /* @__PURE__ */ zod
    .object({
        name: zod.string().max(eventDefinitionsCreateBodyNameMax),
        created_at: zod.iso.datetime({ offset: true }).nullish(),
        last_seen_at: zod.iso.datetime({ offset: true }).nullish(),
        tags: zod.array(zod.unknown()).optional(),
        enforcement_mode: zod.enum(['allow', 'reject']).optional().describe('\* `allow` - Allow\n\* `reject` - Reject'),
        primary_property: zod
            .string()
            .max(eventDefinitionsCreateBodyPrimaryPropertyMax)
            .nullish()
            .describe(
                "Name of a single property on this event that PostHog UIs should display alongside the event (for example `$pathname` on `$pageview`). When set, surfaces like the session replay inspector show the property's value next to the event name without the user having to open the event."
            ),
        post_to_slack: zod.boolean().default(eventDefinitionsCreateBodyPostToSlackDefault),
    })
    .describe('Serializer mixin that handles tags for objects.')

export const eventDefinitionsUpdateBodyNameMax = 400

export const eventDefinitionsUpdateBodyPrimaryPropertyMax = 400

export const eventDefinitionsUpdateBodyPostToSlackDefault = false

export const EventDefinitionsUpdateBody = /* @__PURE__ */ zod
    .object({
        name: zod.string().max(eventDefinitionsUpdateBodyNameMax),
        created_at: zod.iso.datetime({ offset: true }).nullish(),
        last_seen_at: zod.iso.datetime({ offset: true }).nullish(),
        tags: zod.array(zod.unknown()).optional(),
        enforcement_mode: zod.enum(['allow', 'reject']).optional().describe('\* `allow` - Allow\n\* `reject` - Reject'),
        primary_property: zod
            .string()
            .max(eventDefinitionsUpdateBodyPrimaryPropertyMax)
            .nullish()
            .describe(
                "Name of a single property on this event that PostHog UIs should display alongside the event (for example `$pathname` on `$pageview`). When set, surfaces like the session replay inspector show the property's value next to the event name without the user having to open the event."
            ),
        post_to_slack: zod.boolean().default(eventDefinitionsUpdateBodyPostToSlackDefault),
    })
    .describe('Serializer mixin that handles tags for objects.')

export const eventDefinitionsPartialUpdateBodyNameMax = 400

export const eventDefinitionsPartialUpdateBodyPrimaryPropertyMax = 400

export const eventDefinitionsPartialUpdateBodyPostToSlackDefault = false

export const EventDefinitionsPartialUpdateBody = /* @__PURE__ */ zod
    .object({
        name: zod.string().max(eventDefinitionsPartialUpdateBodyNameMax).optional(),
        created_at: zod.iso.datetime({ offset: true }).nullish(),
        last_seen_at: zod.iso.datetime({ offset: true }).nullish(),
        tags: zod.array(zod.unknown()).optional(),
        enforcement_mode: zod.enum(['allow', 'reject']).optional().describe('\* `allow` - Allow\n\* `reject` - Reject'),
        primary_property: zod
            .string()
            .max(eventDefinitionsPartialUpdateBodyPrimaryPropertyMax)
            .nullish()
            .describe(
                "Name of a single property on this event that PostHog UIs should display alongside the event (for example `$pathname` on `$pageview`). When set, surfaces like the session replay inspector show the property's value next to the event name without the user having to open the event."
            ),
        post_to_slack: zod.boolean().default(eventDefinitionsPartialUpdateBodyPostToSlackDefault),
    })
    .describe('Serializer mixin that handles tags for objects.')

/**
 * Add, remove, or replace tags across multiple event definitions in one request.
 *
 * Overrides ``TaggedItemViewSetMixin.bulk_update_tags``, which assumes integer PKs and runs
 * object-level access-control filtering. Event definitions use UUID PKs and are not an
 * object-level access-controlled resource — project membership (enforced by the viewset) is
 * the only boundary, matching the single-object update path — so this scopes by project and
 * skips the per-object editor check. Tags live on the base ``EventDefinition`` row, so it
 * operates there regardless of the enterprise extension.
 */
export const eventDefinitionsBulkUpdateTagsCreateBodyIdsMax = 500

export const eventDefinitionsBulkUpdateTagsCreateBodyTagsItemMax = 255

export const eventDefinitionsBulkUpdateTagsCreateBodyTagsMax = 100

export const EventDefinitionsBulkUpdateTagsCreateBody = /* @__PURE__ */ zod
    .object({
        ids: zod
            .array(zod.uuid())
            .max(eventDefinitionsBulkUpdateTagsCreateBodyIdsMax)
            .describe('List of object UUIDs to update tags on.'),
        action: zod
            .enum(['add', 'remove', 'set'])
            .describe('\* `add` - add\n\* `remove` - remove\n\* `set` - set')
            .describe(
                "'add' merges with existing tags, 'remove' deletes specific tags, 'set' replaces all tags.\n\n\* `add` - add\n\* `remove` - remove\n\* `set` - set"
            ),
        tags: zod
            .array(zod.string().max(eventDefinitionsBulkUpdateTagsCreateBodyTagsItemMax))
            .max(eventDefinitionsBulkUpdateTagsCreateBodyTagsMax)
            .describe('Tag names to add, remove, or set (up to 100 per request, 255 characters each).'),
    })
    .describe('Variant of ``BulkUpdateTagsRequestSerializer`` for resources keyed by UUID (e.g. event definitions).')

/**
 * Mark multiple event definitions as verified or unverified in one request.
 *
 * Verifying event definitions requires an enterprise license, so this action returns a validation error.
 */
export const eventDefinitionsBulkUpdateVerifiedCreateBodyIdsMax = 500

export const EventDefinitionsBulkUpdateVerifiedCreateBody = /* @__PURE__ */ zod.object({
    ids: zod
        .array(zod.uuid())
        .max(eventDefinitionsBulkUpdateVerifiedCreateBodyIdsMax)
        .describe('List of event definition UUIDs to update.'),
    verified: zod
        .boolean()
        .describe(
            'Target verified state to apply to every matched event. `true` marks the events as verified (and unhides them, since an event cannot be both hidden and verified); `false` unverifies them.'
        ),
})
