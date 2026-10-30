import type { Stripe, StripeElements } from '@stripe/stripe-js'
import { waitFor } from '@testing-library/react'
/* oxlint-disable react-hooks/rules-of-hooks -- useMocks is a test helper, not a React hook */
import { router } from 'kea-router'
import { expectLogic } from 'kea-test-utils'
import posthog from 'posthog-js'

// Imported from the source module rather than the `@posthog/lemon-ui` barrel so that the
// spy below replaces `.error` on the same `lemonToast` singleton that `paymentEntryLogic`
// calls at runtime. `jest.mock('@posthog/lemon-ui', ...)` did not propagate through the
// barrel's re-export chain — spying on the shared object avoids that issue.
import { lemonToast } from 'lib/lemon-ui/LemonToast/LemonToast'
import { billingLogic } from 'scenes/billing/billingLogic'
import { PAYMENTS_UNAVAILABLE, paymentEntryLogic } from 'scenes/billing/paymentEntryLogic'
import { organizationLogic } from 'scenes/organizationLogic'
import { userLogic } from 'scenes/userLogic'

import { useMocks } from '~/mocks/jest'
import { initKeaTests } from '~/test/init'
import { BillingProvider, BillingType } from '~/types'

const OTHER_ORGANIZATION_ID = '00000000-0000-4000-8000-000000000002'

const seedBilling = async (billing: Partial<BillingType> | null): Promise<void> => {
    useMocks({ get: { '/api/billing': () => [200, billing ?? {}] } })
    billingLogic.mount()
    await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
}

const stubLocation = (): { href: string } => {
    const location = { ...window.location, href: window.location.href }
    jest.spyOn(window, 'location', 'get').mockReturnValue(location)
    return location
}

const deferred = <T>(): { promise: Promise<T>; resolve: (value: T) => void; reject: (error: unknown) => void } => {
    let resolve!: (value: T) => void
    let reject!: (error: unknown) => void
    const promise = new Promise<T>((res, rej) => {
        resolve = res
        reject = rej
    })
    return { promise, resolve, reject }
}

const fakeStripe = (confirmPayment: () => Promise<unknown>): Stripe => ({ confirmPayment }) as unknown as Stripe
const fakeElements = {} as StripeElements

describe('paymentEntryLogic', () => {
    let logic: ReturnType<typeof paymentEntryLogic.build>
    let toastErrorSpy: jest.SpyInstance
    let toastInfoSpy: jest.SpyInstance

    beforeEach(() => {
        initKeaTests()
        toastErrorSpy = jest.spyOn(lemonToast, 'error').mockImplementation(() => ({ id: 'x' }) as any)
        toastInfoSpy = jest.spyOn(lemonToast, 'info').mockImplementation(() => ({ id: 'x' }) as any)
    })

    afterEach(() => {
        logic?.unmount()
        jest.restoreAllMocks()
        jest.useRealTimers()
        window.history.replaceState({}, '', '/')
    })

    describe('startPaymentEntryFlow — returning customer (customer_id present)', () => {
        it('shows the unavailable toast instead of opening the payment modal', async () => {
            await seedBilling({ customer_id: 'cus_test', subscription_level: 'free' })
            logic = paymentEntryLogic()
            logic.mount()

            await expectLogic(logic, () => logic.actions.startPaymentEntryFlow()).toFinishAllListeners()

            expect(toastErrorSpy).toHaveBeenCalledWith(PAYMENTS_UNAVAILABLE)
            expect(logic.values.paymentEntryModalOpen).toBe(false)
            expect(logic.values.apiError).toBe(null)
        })
    })

    describe('startPaymentEntryFlow — new customer (no customer_id)', () => {
        it('opens the payment entry modal without calling activate', async () => {
            await seedBilling({ subscription_level: 'free' })
            const activate = jest.fn(() => [200, { success: true }] as [number, Record<string, unknown>])
            useMocks({ post: { '/api/billing/activate': activate } })
            logic = paymentEntryLogic()
            logic.mount()

            await expectLogic(logic, () => logic.actions.startPaymentEntryFlow(null, '/foo')).toFinishAllListeners()

            expect(activate).not.toHaveBeenCalled()
            expect(logic.values.paymentEntryModalOpen).toBe(true)
            expect(logic.values.redirectPath).toBe('/foo')
            expect(toastErrorSpy).not.toHaveBeenCalled()
        })
    })

    describe('startPaymentEntryFlow — billing locked outside PostHog', () => {
        it.each<{ name: string; billing: Partial<BillingType> }>([
            {
                name: 'a partner manages billing',
                billing: {
                    subscription_level: 'free',
                    billing_managed_by_partner: { partner_name: 'Example Partner' },
                },
            },
            {
                name: 'Vercel bills an organization with no active subscription',
                billing: {
                    customer_id: 'cus_test',
                    subscription_level: 'free',
                    has_active_subscription: false,
                    billing_provider: BillingProvider.Vercel,
                },
            },
        ])('neither activates nor opens the payment modal when $name', async ({ billing }) => {
            await seedBilling(billing)
            const activate = jest.fn(() => [200, { success: true }] as [number, Record<string, unknown>])
            useMocks({ post: { '/api/billing/activate': activate } })
            logic = paymentEntryLogic()
            logic.mount()

            await expectLogic(logic, () => logic.actions.startPaymentEntryFlow(null, '/foo')).toFinishAllListeners()

            expect(activate).not.toHaveBeenCalled()
            expect(logic.values.paymentEntryModalOpen).toBe(false)
        })
    })

    describe('completion after an organization switch', () => {
        it('switches to the paid organization from the completion modal', async () => {
            await seedBilling({ customer_id: 'cus_original', subscription_level: 'free' })
            const original = organizationLogic.values.currentOrganization!
            const selected = { ...original, id: '00000000-0000-4000-8000-000000000002', name: 'Selected organization' }
            logic = paymentEntryLogic()
            logic.mount()
            organizationLogic.actions.loadCurrentOrganizationSuccess(selected)
            logic.actions.setCompletedPaymentOrganization({ id: original.id, name: original.name })
            // The cached user still names A, so userLogic.updateCurrentOrganization would skip the switch.
            expect(userLogic.values.user?.organization?.id).toBe(original.id)
            const switches: unknown[] = []
            useMocks({
                patch: {
                    '/api/users/@me': async ({ request }) => {
                        switches.push(await request.json())
                        return [200, userLogic.values.user]
                    },
                },
            })
            const location = stubLocation()
            await expectLogic(logic, () => logic.actions.viewCompletedPaymentOrganization()).toFinishAllListeners()
            expect(switches).toEqual([{ set_current_organization: original.id }])
            expect(location.href).toBe('/organization/billing')
        })

        it('stays on the page when switching to the paid organization fails', async () => {
            useMocks({ patch: { '/api/users/@me': () => [500, { detail: 'A server error occurred.' }] } })
            logic = paymentEntryLogic()
            logic.mount()
            logic.actions.setCompletedPaymentOrganization({ id: OTHER_ORGANIZATION_ID, name: 'Original organization' })
            const location = stubLocation()
            const href = location.href
            await expectLogic(logic, () => logic.actions.viewCompletedPaymentOrganization()).toFinishAllListeners()
            expect(toastErrorSpy).toHaveBeenCalledWith('Could not switch organization. Try again.')
            expect(location.href).toBe(href)
        })
    })

    describe('payment flow organization binding', () => {
        it('applies the paid organization to the latest user state', async () => {
            await seedBilling({ subscription_level: 'free' })
            const organization = organizationLogic.values.currentOrganization!
            const user = userLogic.values.user!
            const response = deferred<[number, unknown]>()
            let requested = false
            useMocks({
                get: {
                    [`/api/organizations/${organization.id}`]: () => {
                        requested = true
                        return response.promise
                    },
                },
            })
            logic = paymentEntryLogic()
            logic.mount()
            logic.actions.beginPaymentFlow(organization.id)
            logic.actions.completePaymentFlow(null, { success: true })
            await waitFor(() => expect(requested).toBe(true))
            userLogic.actions.loadUserSuccess({ ...user, first_name: 'Updated name' })
            response.resolve([200, { ...organization, customer_id: 'cus_refreshed' }])
            await expectLogic(logic).toFinishAllListeners()
            expect(userLogic.values.user?.first_name).toBe('Updated name')
            expect(userLogic.values.user?.organization?.customer_id).toBe('cus_refreshed')
            expect(organizationLogic.values.currentOrganization?.customer_id).toBe('cus_refreshed')
        })

        it('applies nothing when another organization is selected while the paid organization loads', async () => {
            await seedBilling({ subscription_level: 'free' })
            const original = organizationLogic.values.currentOrganization!
            const user = userLogic.values.user!
            const billingBefore = billingLogic.values.billing
            const organizationResponse = deferred<[number, unknown]>()
            let requested = false
            useMocks({
                get: {
                    '/api/billing': () => [200, { subscription_level: 'paid', customer_id: 'cus_paid' }],
                    [`/api/organizations/${original.id}`]: () => {
                        requested = true
                        return organizationResponse.promise
                    },
                },
            })
            logic = paymentEntryLogic()
            logic.mount()
            logic.actions.beginPaymentFlow(original.id)
            logic.actions.completePaymentFlow(null, { success: true })
            await waitFor(() => expect(requested).toBe(true))
            const selected = { ...original, id: OTHER_ORGANIZATION_ID }
            organizationLogic.actions.loadCurrentOrganizationSuccess(selected)
            userLogic.actions.loadUserSuccess({ ...user, first_name: 'Updated name', organization: selected })
            organizationResponse.resolve([200, { ...original, customer_id: 'cus_refreshed' }])
            await expectLogic(logic).toFinishAllListeners()
            expect(billingLogic.values.billing).toBe(billingBefore)
            expect(organizationLogic.values.currentOrganization).toEqual(selected)
            expect(userLogic.values.user).toMatchObject({ first_name: 'Updated name', organization: selected })
            expect(logic.values.completedPaymentOrganization).toEqual({ id: original.id, name: original.name })
        })

        it('restores the organization and redirect from the Stripe callback', async () => {
            const organizationId = '00000000-0000-4000-8000-000000000002'
            const redirectPath = '/project/2/replay?foo=bar'
            window.history.replaceState(
                {},
                '',
                `/?organization_id=${organizationId}&postRedirectPath=${encodeURIComponent(redirectPath)}`
            )
            logic = paymentEntryLogic()
            logic.mount()
            expect(logic.values.paymentOrganizationId).toBe(organizationId)
            const returnUrl = new URL(logic.values.stripeReturnUrl!)
            expect(returnUrl.pathname).toBe('/billing/authorization_status')
            expect(returnUrl.searchParams.get('organization_id')).toBe(organizationId)
            expect(returnUrl.searchParams.get('postRedirectPath')).toBe(redirectPath)
        })

        it.each(['', '?organization_id=invalid', '?organization_id=@current'])(
            'rejects old or invalid callbacks %s without polling',
            async (query) => {
                const statusRequest = jest.fn(() => [200, { status: 'success' }])
                useMocks({ post: { '/api/billing/activate/authorize/status': statusRequest } })
                window.history.replaceState({}, '', `/${query}`)
                logic = paymentEntryLogic()
                logic.mount()
                await expectLogic(logic, () => logic.actions.pollAuthorizationStatus('pi_test')).toFinishAllListeners()
                expect(statusRequest).not.toHaveBeenCalled()
                expect(logic.values.apiError).toContain('Return to billing and start again')
            }
        )

        it('clears the previous secret when a new flow starts', () => {
            logic = paymentEntryLogic()
            logic.mount()
            logic.actions.beginPaymentFlow('00000000-0000-4000-8000-000000000001')
            logic.actions.setClientSecret('secret_previous')
            logic.actions.beginPaymentFlow('00000000-0000-4000-8000-000000000002')
            expect(logic.values.clientSecret).toBe(null)
        })
    })

    describe('closing the modal after the card is submitted', () => {
        const submitCard = (): void =>
            logic.actions.confirmPayment(
                fakeStripe(async () => ({ paymentIntent: { id: 'pi_submitted' } })),
                fakeElements
            )

        const startAgainAndExpectRefusal = (): void => {
            const flow = logic.values.paymentFlow
            logic.actions.startPaymentEntryFlow(null, '/project/1/replay')
            expect(toastInfoSpy).toHaveBeenCalledWith("We're still confirming your last payment.")
            expect(logic.values.paymentEntryModalOpen).toBe(false)
            expect(logic.values.paymentFlow).toBe(flow)
        }

        beforeEach(async () => {
            await seedBilling({ subscription_level: 'free' })
            logic = paymentEntryLogic()
            logic.mount()
            logic.actions.beginPaymentFlow(organizationLogic.values.currentOrganization!.id, '/project/1/replay')
            logic.actions.showPaymentEntryModal()
        })

        it('ends the flow when the modal closes after the card is declined', async () => {
            logic.actions.setClientSecret('secret_submitted')
            logic.actions.confirmPayment(
                fakeStripe(async () => ({ error: { message: 'Your card was declined.' } })),
                fakeElements
            )
            await expectLogic(logic).toFinishAllListeners()
            // The card form stays so the decline shows and another card can be tried.
            expect(logic.values).toMatchObject({
                stripeError: 'Your card was declined.',
                isLoading: false,
                clientSecret: 'secret_submitted',
            })
            logic.actions.hidePaymentEntryModal()
            expect(logic.values.paymentFlow).toBe(null)
        })

        it('refuses a second start while the confirmation is pending', async () => {
            const confirmation = deferred<unknown>()
            logic.actions.confirmPayment(
                fakeStripe(() => confirmation.promise),
                fakeElements
            )
            logic.actions.hidePaymentEntryModal()
            startAgainAndExpectRefusal()
            confirmation.resolve({ paymentIntent: { id: 'pi_submitted' } })
            await expectLogic(logic).toFinishAllListeners()
            expect(logic.values.paymentSubmitted).toBe(false)
        })

        it('lets the next start begin after a failed payment is closed', async () => {
            submitCard()
            await expectLogic(logic).toFinishAllListeners()
            logic.actions.hidePaymentEntryModal()
            logic.actions.startPaymentEntryFlow(null, '/project/1/replay')
            expect(toastInfoSpy).not.toHaveBeenCalled()
            expect(logic.values.paymentEntryModalOpen).toBe(true)
        })
    })

    describe('a payment step that settles after it was superseded', () => {
        type Outcome = 'resolves' | 'rejects'
        interface PendingStep {
            start: () => void
            requested: () => boolean
            settle: (outcome: Outcome) => void
        }

        const pendingRead = (url: string, body: unknown): Omit<PendingStep, 'start'> => {
            const response = deferred<[number, unknown]>()
            let requested = false
            useMocks({
                get: {
                    [url]: () => {
                        requested = true
                        return response.promise
                    },
                },
            })
            return {
                requested: () => requested,
                settle: (outcome) =>
                    response.resolve(outcome === 'resolves' ? [200, body] : [500, { detail: 'Server error' }]),
            }
        }

        const steps: Record<string, (organizationId: string) => PendingStep> = {
            'card confirmation': (organizationId) => {
                const confirmation = deferred<unknown>()
                let requested = false
                const stripe = fakeStripe(() => {
                    requested = true
                    return confirmation.promise
                })
                return {
                    start: () => {
                        logic.actions.beginPaymentFlow(organizationId)
                        logic.actions.confirmPayment(stripe, fakeElements)
                    },
                    requested: () => requested,
                    settle: (outcome) =>
                        outcome === 'resolves'
                            ? confirmation.resolve({ paymentIntent: { id: 'pi_stale' } })
                            : confirmation.reject(new Error('Network error')),
                }
            },
            'organization read': (organizationId) => ({
                ...pendingRead(`/api/organizations/${organizationId}`, {
                    ...organizationLogic.values.currentOrganization,
                    name: 'Stale name',
                }),
                start: () => {
                    logic.actions.beginPaymentFlow(organizationId)
                    logic.actions.completePaymentFlow(null, { success: true })
                },
            }),
        }

        let captureSpy: jest.SpyInstance
        let pushSpy: jest.SpyInstance

        beforeEach(async () => {
            await seedBilling({ customer_id: 'cus_test', subscription_level: 'free' })
            captureSpy = jest.spyOn(posthog, 'captureException').mockImplementation(() => undefined as any)
            pushSpy = jest.spyOn(router.actions, 'push')
            logic = paymentEntryLogic()
            logic.mount()
        })

        const snapshot = (): Record<string, unknown> => ({
            payment: Object.fromEntries(
                Object.keys(paymentEntryLogic.selectors).map((key) => [key, (logic.values as any)[key]])
            ),
            billing: billingLogic.values.billing,
            organization: organizationLogic.values.currentOrganization,
            user: userLogic.values.user,
        })

        const sideEffects = (): Record<string, unknown[]> => ({
            toasts: toastErrorSpy.mock.calls,
            captures: captureSpy.mock.calls,
            navigations: pushSpy.mock.calls,
        })

        const settleLate = async (
            step: PendingStep,
            outcome: Outcome,
            supersede: () => void
        ): Promise<{ before: unknown; after: unknown; sideEffects: Record<string, unknown[]> }> => {
            step.start()
            await waitFor(() => expect(step.requested()).toBe(true))
            supersede()
            const before = snapshot()
            step.settle(outcome)
            await expectLogic(logic).toFinishAllListeners()
            return { before, after: snapshot(), sideEffects: sideEffects() }
        }
        const NO_SIDE_EFFECTS = { toasts: [], captures: [], navigations: [] }

        const cases = Object.keys(steps).flatMap((name) =>
            (['resolves', 'rejects'] as const).map((outcome) => [name, outcome] as const)
        )

        it.each(cases)('%s that %s after a new flow starts changes nothing', async (name, outcome) => {
            const step = steps[name](organizationLogic.values.currentOrganization!.id)
            const { before, after, sideEffects } = await settleLate(step, outcome, () =>
                logic.actions.beginPaymentFlow(OTHER_ORGANIZATION_ID)
            )
            expect(after).toEqual(before)
            expect(sideEffects).toEqual(NO_SIDE_EFFECTS)
        })
    })
})
