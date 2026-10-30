import { router } from 'kea-router'
import { expectLogic } from 'kea-test-utils'

import { dayjs } from 'lib/dayjs'
import { lemonToast } from 'lib/lemon-ui/LemonToast/LemonToast'
import { dateMapping } from 'lib/utils/dateFilters'
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
import { BillingSpendResponse, BillingSpendResponseBreakdownType, billingSpendLogic } from './billingSpendLogic'
import { fitsOneRequest, isDayOrCoarser, SUB_DAY_DATE_FILTER_INTERVALS } from './billingUsageLogic'
import type { BillingFilters } from './types'

describe('billingSpendLogic chart type', () => {
    let logic: ReturnType<typeof billingSpendLogic.build>

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
        logic = billingSpendLogic()
        logic.mount()
        await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()
    }

    beforeEach(() => {
        initKeaTests()
    })

    afterEach(() => {
        logic?.unmount()
    })

    it('always allows stacking, because spend is dollars in every breakdown', async () => {
        useMocks(mocks())
        await mount()

        expect(logic.values.canStackSeries).toBe(true)
    })

    it('defaults to stacked bars once the breakdown is by project', async () => {
        // A stacked bar shows the bill and the projects it is made of; a line shows neither, so the
        // default with a project breakdown is a bar.
        useMocks(mocks())
        await mount()

        logic.actions.setFilters({ breakdowns: ['type', 'team'] })

        expect(logic.values.effectiveChartType).toBe('bar')
    })

    it('defaults to a line without a project breakdown, where there is nothing to compose', async () => {
        useMocks(mocks())
        await mount()

        logic.actions.setFilters({ breakdowns: ['type'] })

        expect(logic.values.effectiveChartType).toBe('line')
    })

    it('keeps a chosen type when the breakdown changes the default underneath it', async () => {
        // The stored value is null until someone picks, so the default can follow the breakdown.
        // Once they pick, that choice outranks the default rather than being overwritten by it.
        useMocks(mocks())
        await mount()

        logic.actions.setChartType('line')
        logic.actions.setFilters({ breakdowns: ['type', 'team'] })

        expect(logic.values.effectiveChartType).toBe('line')
    })

    describe('toggleAllSeries', () => {
        const spendResponse = (totals: number[]): BillingSpendResponse => ({
            count: totals.length,
            next: null,
            previous: null,
            results: totals.map((total, id) => ({
                id,
                label: `series ${id}`,
                data: [total],
                dates: ['2026-08-01'],
                breakdown_type: BillingSpendResponseBreakdownType.MULTIPLE,
                breakdown_value: ['product_analytics', String(id)],
            })),
        })

        it('hides every series when all are visible, then shows them all again', async () => {
            useMocks(mocks())
            await mount()
            logic.actions.loadBillingSpendSuccess(spendResponse([1, 2, 3]))

            logic.actions.toggleAllSeries()
            expect(logic.values.userHiddenSeries).toEqual([0, 1, 2])

            logic.actions.toggleAllSeries()
            expect(logic.values.userHiddenSeries).toEqual([])
        })

        it('shows all when only some are hidden', async () => {
            useMocks(mocks())
            await mount()
            logic.actions.loadBillingSpendSuccess(spendResponse([1, 2, 3]))

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
            useMocks(mocks())
            await mount()
            logic.actions.loadBillingSpendSuccess(spendResponse([0, 2, 3]))
            logic.actions.setExcludeEmptySeries(true, false)
            hiddenByHand.forEach((id) => logic.actions.toggleSeries(id))

            logic.actions.toggleAllSeries()

            expect(logic.values.userHiddenSeries).toEqual(expected)
            expect(new Set(logic.values.finalHiddenSeries)).toEqual(new Set([0, 1, 2]))
        })
    })
})

describe('billing date options', () => {
    // "Last hour" reached the API as `start_date=-1h`, which is not a date, so billing read the
    // range as backwards and rejected the whole request with "start_date must be before or equal
    // to end_date". A filter that only excluded 'hour' intervals would let it through, because
    // "Last hour" is a 'minute' one.
    it('offers nothing finer than a day, whatever interval the option declares', () => {
        const subDay = dateMapping.filter(
            (option) => option.defaultInterval && SUB_DAY_DATE_FILTER_INTERVALS.includes(option.defaultInterval)
        )
        expect(subDay.length).toBeGreaterThan(0)
        expect(subDay.map((option) => option.key)).toContain('Last hour')
        expect(subDay.filter(isDayOrCoarser)).toEqual([])
    })

    it('keeps the day and month options', () => {
        const kept = dateMapping.filter(isDayOrCoarser).map((option) => option.key)
        expect(kept).toContain('Last 7 days')
        expect(kept).toContain('Last 30 days')
        expect(kept).not.toContain('Last hour')
        expect(kept).not.toContain('Last 24 hours')
    })

    it('does not offer All time, since billing serves at most a year per request', () => {
        const offered = dateMapping
            .filter(isDayOrCoarser)
            .filter(fitsOneRequest)
            .map((option) => option.key)
        expect(dateMapping.map((option) => option.key)).toContain('All time')
        expect(offered).not.toContain('All time')
        expect(offered).toContain('This year')
        expect(offered).toContain('Last 180 days')
    })
})

describe('billing spend load triggers', () => {
    let logic: ReturnType<typeof billingSpendLogic.build>

    beforeEach(() => {
        initKeaTests()
        useMocks({ get: { '/api/billing': () => [200, billingJson] } })
    })

    afterEach(() => {
        logic?.unmount()
        jest.restoreAllMocks()
    })

    const spendParams = (spy: jest.SpyInstance): BillingReadParams[] => spy.mock.calls.map(([params]) => params)

    // The unavailable reads return no export URL, so the export selectors would only ever read
    // null. Echo the params instead, to see what each export would ask for.
    const echoExportParams = (): void => {
        jest.spyOn(unavailableBillingReads, 'spendExportUrl').mockImplementation((params) => JSON.stringify(params))
    }
    const exportParams = (url: string | null): BillingReadParams => JSON.parse(url ?? '{}')

    // afterMount, and urlToAction once for the filters and once for the dates, each ask to load on
    // arrival. The breakpoint must keep only the last call, and that call must carry the dates from
    // the URL. Billing loads before the mount here, so the billing subscriptions do not fire.
    it('takes the filters and dates from the URL on arrival', async () => {
        const spendSeries = jest.spyOn(unavailableBillingReads, 'spendSeries')
        router.actions.push(urls.organizationBillingSection('spend'), {
            breakdowns: ['type', 'team'],
            date_from: '2026-01-01',
        })
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()

        logic = billingSpendLogic({ syncWithUrl: true })
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual('2026-01-01')
        expect(logic.values.filters.breakdowns).toEqual(['type', 'team'])
        expect(spendParams(spendSeries)).toHaveLength(1)
        expect(spendParams(spendSeries)[0].start_date).toEqual('2026-01-01')
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
            const spendSeries = jest.spyOn(unavailableBillingReads, 'spendSeries')
            echoExportParams()
            billingLogic.mount()
            await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
            logic = billingSpendLogic({ initialFilters: { breakdowns, top_projects: topProjects } })
            logic.mount()
            await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()

            const calls = spendParams(spendSeries)
            expect(calls).toHaveLength(1)
            expect(calls[0].top_projects).toEqual(expected)
            expect(exportParams(logic.values.spendChartExportUrl).top_projects).toEqual(expected)
            expect(exportParams(logic.values.spendExportUrl).top_projects).toBeUndefined()
        }
    )

    it('keeps an open-ended preset open, and asks for a range that ends yesterday', async () => {
        // "This year" carries only a start. The picker recognises its own preset only while the
        // end stays empty; with yesterday filled in it would read back as "No date range override".
        const spendSeries = jest.spyOn(unavailableBillingReads, 'spendSeries')
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingSpendLogic({})
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        logic.actions.setDateRange('yStart', null, false)
        await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual('yStart')
        expect(logic.values.dateTo).toBeNull()
        const calls = spendParams(spendSeries)
        expect(calls[calls.length - 1].end_date).toEqual(dayjs().subtract(1, 'day').format('YYYY-MM-DD'))
    })

    it('shows the unavailable reads in the page rather than as a failure toast', async () => {
        const toastError = jest.spyOn(lemonToast, 'error')
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingSpendLogic()
        logic.mount()
        await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()

        expect(logic.values.billingSpendError).toEqual({
            code: BILLING_READS_UNAVAILABLE_CODE,
            detail: BILLING_READS_UNAVAILABLE,
        })
        expect(toastError).not.toHaveBeenCalled()
    })
})
