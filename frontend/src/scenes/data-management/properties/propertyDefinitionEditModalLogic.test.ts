import { expectLogic } from 'kea-test-utils'

import { useMocks } from '~/mocks/jest'
import { initKeaTests } from '~/test/init'

import { PropertyDefinitionEditModalProps, propertyDefinitionEditModalLogic } from './propertyDefinitionEditModalLogic'

describe('propertyDefinitionEditModalLogic', () => {
    it('saves the editable definition fields', async () => {
        let requestBody: unknown
        const onClose = jest.fn()
        const onSave = jest.fn()
        const propertyDefinition = {
            id: 'property-id',
            name: 'plan',
            tags: ['billing'],
            property_type: 'String',
        } as PropertyDefinitionEditModalProps['propertyDefinition']

        useMocks({
            patch: {
                '/api/projects/:team/property_definitions/:id/': async ({ request }) => {
                    requestBody = await request.json()
                    return [200, { ...propertyDefinition, ...(requestBody as object) }]
                },
            },
        })
        initKeaTests()

        const logic = propertyDefinitionEditModalLogic({ propertyDefinition, onClose, onSave })
        logic.mount()
        logic.actions.setPropertyDefinitionEditFormValues({
            property_type: 'Boolean',
            tags: ['billing', 'reporting'],
        })

        await expectLogic(logic, () => logic.actions.submitPropertyDefinitionEditForm())
            .toDispatchActions(['submitPropertyDefinitionEditFormSuccess'])
            .toFinishAllListeners()

        expect(requestBody).toEqual({
            property_type: 'Boolean',
            tags: ['billing', 'reporting'],
        })
        expect(onSave).toHaveBeenCalledWith(expect.objectContaining(requestBody as object))
        expect(onClose).not.toHaveBeenCalled()

        logic.unmount()
    })
})
