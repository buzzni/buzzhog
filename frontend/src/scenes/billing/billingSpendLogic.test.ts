import { router } from 'kea-router'
import { expectLogic } from 'kea-test-utils'

import { dateMapping } from 'lib/utils/dateFilters'
import { billingLogic } from 'scenes/billing/billingLogic'
import { urls } from 'scenes/urls'

import { billingJson } from '~/mocks/fixtures/_billing'
import { useMocks } from '~/mocks/jest'
import { initKeaTests } from '~/test/init'

import { unavailableBillingReads } from './billingReads'
import { BillingSpendResponse, BillingSpendResponseBreakdownType, billingSpendLogic } from './billingSpendLogic'
import { fitsOneRequest, isDayOrCoarser, SUB_DAY_DATE_FILTER_INTERVALS } from './billingUsageLogic'

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

        it('ignores empty series when they are excluded', async () => {
            // Empty series are hidden by the exclusion already, so they must not keep "all visible" false.
            useMocks(mocks())
            await mount()
            logic.actions.loadBillingSpendSuccess(spendResponse([0, 2, 3]))
            logic.actions.setExcludeEmptySeries(true, false)

            logic.actions.toggleAllSeries()

            expect(logic.values.userHiddenSeries).toEqual([1, 2])
            expect(logic.values.finalHiddenSeries.sort()).toEqual([0, 1, 2])
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

    const spendParams = (spy: jest.SpyInstance): Record<string, string | number>[] =>
        spy.mock.calls.map(([params]) => params)

    // afterMount, urlToAction reading the filters out of the URL, and the subscriptions that fire
    // once billing says the plan is not hobby all want to load on arrival. The breakpoint must
    // keep only the last call, and that call must carry the dates from the URL.
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

    it.each([
        ['with a project breakdown', ['type', 'team'] as ('type' | 'team')[], 20, '20'],
        ['without a project breakdown', ['type'] as ('type' | 'team')[], 20, undefined],
        ['when the cap is off', ['type', 'team'] as ('type' | 'team')[], null, undefined],
    ])('sends the project cap only where it ranks something, %s', async (_name, breakdowns, topProjects, expected) => {
        const spendSeries = jest.spyOn(unavailableBillingReads, 'spendSeries')
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingSpendLogic({ initialFilters: { breakdowns, top_projects: topProjects } })
        logic.mount()
        await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()

        const calls = spendParams(spendSeries)
        expect(calls).toHaveLength(1)
        expect(calls[0].top_projects).toEqual(expected === undefined ? undefined : Number(expected))
    })

    it('exports every project, and the chart export keeps the cap', async () => {
        const spendExportUrl = jest.spyOn(unavailableBillingReads, 'spendExportUrl')
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingSpendLogic({ initialFilters: { breakdowns: ['type', 'team'], top_projects: 20 } })
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        void logic.values.spendExportUrl
        void logic.values.spendChartExportUrl

        const exported = spendExportUrl.mock.calls.map(([params]) => params)
        expect(exported.map((params) => params.top_projects)).toEqual([undefined, 20])
    })

    it('keeps an open-ended preset open', async () => {
        // "This year" carries only a start. The picker recognises its own preset only while the
        // end stays empty; with yesterday filled in it would read back as "No date range override".
        billingLogic.mount()
        await expectLogic(billingLogic, () => billingLogic.actions.loadBilling()).toFinishAllListeners()
        logic = billingSpendLogic({})
        logic.mount()
        await expectLogic(logic).toFinishAllListeners()

        logic.actions.setDateRange('yStart', null, false)
        await expectLogic(logic).toDispatchActions(['loadBillingSpendSuccess']).toFinishAllListeners()

        expect(logic.values.dateFrom).toEqual('yStart')
        expect(logic.values.dateTo).toBeNull()
    })
})
