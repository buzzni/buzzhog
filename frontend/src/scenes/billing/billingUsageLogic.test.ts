import { router } from 'kea-router'
import { expectLogic } from 'kea-test-utils'

import { lemonToast } from 'lib/lemon-ui/LemonToast/LemonToast'
import { billingLogic } from 'scenes/billing/billingLogic'
import { urls } from 'scenes/urls'

import { billingJson } from '~/mocks/fixtures/_billing'
import { useMocks } from '~/mocks/jest'
import { initKeaTests } from '~/test/init'

import {
    BILLING_READS_UNAVAILABLE,
    BILLING_READS_UNAVAILABLE_CODE,
    BillingReadParams,
    unavailableBillingReads,
} from './billingReads'
import {
    BILLING_USAGE_QUERY_TOO_LARGE_CODE,
    BillingUsageResponse,
    BillingUsageResponseBreakdownType,
    convertDesktopUsageSeries,
    getBillingUsageError,
    billingUsageLogic,
} from './billingUsageLogic'
import type { BillingFilters } from './types'

const series = (label: string, usageType: string, data: number[]): BillingUsageResponse['results'][number] => ({
    id: 1,
    label,
    data,
    dates: ['2026-08-01'],
    breakdown_type: BillingUsageResponseBreakdownType.TYPE,
    breakdown_value: usageType,
})

describe('convertDesktopUsageSeries', () => {
    it.each([
        [
            'PostHog Desktop token credits',
            'posthog_code_token_credits_used_in_period',
            1234,
            12.34,
            'PostHog Desktop token spend (USD)',
        ],
        ['Sandbox compute credits', 'sandbox_compute_credits_used_in_period', 266, 2.66, 'Cloud compute spend (USD)'],
        [
            'Sandbox compute CPU millicore-seconds',
            'sandbox_compute_cpu_millicore_seconds_in_period',
            1500,
            1.5,
            'Cloud compute CPU (core-seconds)',
        ],
        [
            'Sandbox compute memory MiB-seconds',
            'sandbox_compute_memory_mib_seconds_in_period',
            4608,
            4.5,
            'Cloud compute memory (GiB-seconds)',
        ],
    ])('converts %s without changing missing points', (label, usageType, input, output, expectedLabel) => {
        expect(convertDesktopUsageSeries(series(label, usageType, [input]))).toMatchObject({
            label: expectedLabel,
            data: [output],
        })
    })

    it('leaves unrelated usage series unchanged', () => {
        const input = series('Events', 'events', [10])
        expect(convertDesktopUsageSeries(input)).toBe(input)
    })

    it('converts a project breakdown and preserves its label', () => {
        const input = {
            ...series('my-project::PostHog Desktop token credits', 'posthog_code_token_credits_used_in_period', [1234]),
            breakdown_type: BillingUsageResponseBreakdownType.MULTIPLE,
            breakdown_value: ['posthog_code_token_credits_used_in_period', 'my-project'],
        }

        expect(convertDesktopUsageSeries(input)).toMatchObject({
            label: 'my-project::PostHog Desktop token spend (USD)',
            data: [12.34],
        })
    })
})

describe('getBillingUsageError', () => {
    it('preserves the actionable query-size error', () => {
        expect(
            getBillingUsageError({
                code: BILLING_USAGE_QUERY_TOO_LARGE_CODE,
                detail: 'Select a product.',
            })
        ).toEqual({
            code: BILLING_USAGE_QUERY_TOO_LARGE_CODE,
            detail: 'Select a product.',
        })
    })

    it('ignores errors without the expected API shape', () => {
        expect(getBillingUsageError(new Error('request failed'))).toBeNull()
        expect(getBillingUsageError({ code: BILLING_USAGE_QUERY_TOO_LARGE_CODE })).toBeNull()
    })
})

describe('billingUsageLogic loader', () => {
    let logic: ReturnType<typeof billingUsageLogic.build>
    let toastErrorSpy: jest.SpyInstance

    beforeEach(() => {
        initKeaTests()
        toastErrorSpy = jest.spyOn(lemonToast, 'error').mockImplementation(() => ({ id: 'x' }) as any)
    })

    afterEach(() => {
        logic?.unmount()
        toastErrorSpy.mockRestore()
    })

    it('shows the unavailable reads in the page rather than as a failure toast', async () => {
        useMocks({ get: { '/api/billing': () => [200, billingJson] } })

        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()

        logic = billingUsageLogic()
        logic.mount()

        await expectLogic(logic)
            .toDispatchActions(['loadBillingUsageSuccess'])
            .toNotHaveDispatchedActions(['loadBillingUsageFailure'])
            .toFinishAllListeners()

        expect(logic.values.billingUsageError).toEqual({
            code: BILLING_READS_UNAVAILABLE_CODE,
            detail: BILLING_READS_UNAVAILABLE,
        })
        expect(toastErrorSpy).not.toHaveBeenCalled()
    })
})

describe('billingUsageLogic chart type', () => {
    let logic: ReturnType<typeof billingUsageLogic.build>

    // useMocks has to be called straight from the test body: the hooks lint rule rejects a
    // hook-named call inside an ordinary helper.
    const mocks = (): Parameters<typeof useMocks>[0] => ({
        get: {
            '/api/billing': () => [200, billingJson],
        },
    })

    const mount = async (): Promise<void> => {
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingUsageLogic()
        logic.mount()
        await expectLogic(logic).toDispatchActions(['loadBillingUsageSuccess']).toFinishAllListeners()
    }

    beforeEach(() => {
        initKeaTests()
    })

    afterEach(() => {
        logic?.unmount()
    })

    it('will not stack usage types, because they are not the same unit', async () => {
        useMocks(mocks())
        await mount()

        logic.actions.setFilters({ usage_types: ['event_count_in_period', 'recording_count_in_period'] })

        expect(logic.values.canStackSeries).toBe(false)
    })

    it('will stack once a single product is selected', async () => {
        useMocks(mocks())
        await mount()

        logic.actions.setFilters({ usage_types: ['event_count_in_period'] })

        expect(logic.values.canStackSeries).toBe(true)
    })

    it('falls back to a line when bars are asked for but cannot be stacked', async () => {
        // A URL can name a chart type the data does not support, so the guard lives in the
        // selector as well as on the disabled control.
        useMocks(mocks())
        await mount()

        logic.actions.setFilters({ usage_types: ['event_count_in_period', 'recording_count_in_period'] })
        logic.actions.setChartType('bar')

        expect(logic.values.chartType).toBe('bar')
        expect(logic.values.effectiveChartType).toBe('line')
    })

    it('honours bars once the selection makes them meaningful', async () => {
        useMocks(mocks())
        await mount()

        logic.actions.setChartType('bar')
        logic.actions.setFilters({ usage_types: ['event_count_in_period'] })

        expect(logic.values.effectiveChartType).toBe('bar')
    })

    it('defaults to a line', async () => {
        useMocks(mocks())
        await mount()

        expect(logic.values.chartType).toBeNull()
        expect(logic.values.effectiveChartType).toBe('line')
    })
})

describe('billing section URL scoping', () => {
    let logic: ReturnType<typeof billingUsageLogic.build>

    beforeEach(() => {
        initKeaTests()
        useMocks({ get: { '/api/billing': () => [200, billingJson] } })
    })

    afterEach(() => {
        logic?.unmount()
    })

    // The two pages write the same query parameter names, so a logic listening on '*' would
    // read the spend page's filter changes as its own and refetch against them.
    it('ignores filter changes made on the spend page', async () => {
        router.actions.push(urls.organizationBillingSection('usage'))
        logic = billingUsageLogic({ syncWithUrl: true })
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()
        const { dateFrom, filters } = logic.values

        router.actions.push(urls.organizationBillingSection('spend'), {
            breakdowns: ['type', 'team'],
            usage_types: ['event_count_in_period'],
            date_from: '2026-01-01',
        })
        await expectLogic(logic).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual(dateFrom)
        expect(logic.values.filters).toEqual(filters)
    })

    it('still follows filter changes made on its own page', async () => {
        router.actions.push(urls.organizationBillingSection('usage'))
        logic = billingUsageLogic({ syncWithUrl: true })
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        router.actions.push(urls.organizationBillingSection('usage'), { date_from: '2026-01-01' })
        await expectLogic(logic).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual('2026-01-01')
    })
})

describe('billingUsageLogic toggleAllSeries', () => {
    let logic: ReturnType<typeof billingUsageLogic.build>

    const usageResponse = (totals: number[]): BillingUsageResponse => ({
        count: totals.length,
        next: null,
        previous: null,
        results: totals.map((total, id) => ({ ...series(`series ${id}`, 'events', [total]), id })),
    })

    const mountWith = async (totals: number[]): Promise<void> => {
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingUsageLogic()
        logic.mount()
        await expectLogic(logic).toDispatchActions(['loadBillingUsageSuccess']).toFinishAllListeners()
        logic.actions.loadBillingUsageSuccess(usageResponse(totals))
    }

    beforeEach(() => {
        initKeaTests()
        useMocks({ get: { '/api/billing': () => [200, billingJson] } })
    })

    afterEach(() => {
        logic?.unmount()
    })

    it('hides every series when all are visible, then shows them all again', async () => {
        await mountWith([1, 2, 3])

        logic.actions.toggleAllSeries()
        expect(logic.values.userHiddenSeries).toEqual([0, 1, 2])

        logic.actions.toggleAllSeries()
        expect(logic.values.userHiddenSeries).toEqual([])
    })

    it('shows all when only some are hidden', async () => {
        await mountWith([1, 2, 3])

        logic.actions.toggleSeries(1)
        logic.actions.toggleAllSeries()

        expect(logic.values.userHiddenSeries).toEqual([])
    })

    // With the exclusion on, the header checkbox acts only on the series the table can show.
    // An empty series that is also hidden by hand must not stop it from hiding all, and hiding
    // all keeps that id, so the series stays hidden when the exclusion goes off. An empty
    // series that only the exclusion hides stays out of the hand-hidden list.
    it.each<[string, number[], number[]]>([
        ['nothing hidden by hand', [], [1, 2]],
        ['the empty series hidden by hand', [0], [0, 1, 2]],
    ])('hides only the series the exclusion leaves, with %s', async (_name, hiddenByHand, expected) => {
        await mountWith([0, 2, 3])
        logic.actions.setExcludeEmptySeries(true, false)
        hiddenByHand.forEach((id) => logic.actions.toggleSeries(id))

        logic.actions.toggleAllSeries()

        expect(logic.values.userHiddenSeries).toEqual(expected)
        expect(new Set(logic.values.finalHiddenSeries)).toEqual(new Set([0, 1, 2]))
    })
})

describe('billing usage load triggers', () => {
    let logic: ReturnType<typeof billingUsageLogic.build>

    beforeEach(() => {
        initKeaTests()
        useMocks({ get: { '/api/billing': () => [200, billingJson] } })
    })

    afterEach(() => {
        logic?.unmount()
        jest.restoreAllMocks()
    })

    const usageParams = (spy: jest.SpyInstance): BillingReadParams[] => spy.mock.calls.map(([params]) => params)

    // The unavailable reads return no export URL, so the export selectors would only ever read
    // null. Echo the params instead, to see what each export would ask for.
    const echoExportParams = (): void => {
        jest.spyOn(unavailableBillingReads, 'usageExportUrl').mockImplementation((params) => JSON.stringify(params))
    }
    const exportParams = (url: string | null): BillingReadParams => JSON.parse(url ?? '{}')

    // afterMount, and urlToAction once for the filters and once for the dates, each ask to load on
    // arrival. The breakpoint must keep only the last call, and that call must carry the dates from
    // the URL. Billing loads before the mount here, so the billing subscriptions do not fire.
    it('takes the filters and dates from the URL on arrival', async () => {
        const usageSeries = jest.spyOn(unavailableBillingReads, 'usageSeries')
        router.actions.push(urls.organizationBillingSection('usage'), {
            breakdowns: ['type', 'team'],
            date_from: '2026-01-01',
        })
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()

        logic = billingUsageLogic({ syncWithUrl: true })
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual('2026-01-01')
        expect(logic.values.filters.breakdowns).toEqual(['type', 'team'])
        expect(usageParams(usageSeries)).toHaveLength(1)
        expect(usageParams(usageSeries)[0].start_date).toEqual('2026-01-01')
    })

    // The full export holds every project in the period, so it never carries the cap. The chart
    // export holds the series as the chart draws them, so it carries the cap where the request does.
    it.each<[string, BillingFilters['breakdowns'], number | null, number | undefined]>([
        ['with a project breakdown', ['type', 'team'], 20, 20],
        ['without a project breakdown', ['type'], 20, undefined],
        ['when the cap is off', ['type', 'team'], null, undefined],
    ])(
        'sends the project cap only where it ranks something, and never in the full export, %s',
        async (_name, breakdowns, topProjects, expected) => {
            const usageSeries = jest.spyOn(unavailableBillingReads, 'usageSeries')
            echoExportParams()
            billingLogic.mount()
            await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
            logic = billingUsageLogic({ initialFilters: { breakdowns, top_projects: topProjects } })
            logic.mount()
            await expectLogic(logic).toDispatchActions(['loadBillingUsageSuccess']).toFinishAllListeners()

            const calls = usageParams(usageSeries)
            expect(calls).toHaveLength(1)
            expect(calls[0].top_projects).toEqual(expected)
            expect(exportParams(logic.values.usageChartExportUrl).top_projects).toEqual(expected)
            expect(exportParams(logic.values.usageExportUrl).top_projects).toBeUndefined()
        }
    )
})
