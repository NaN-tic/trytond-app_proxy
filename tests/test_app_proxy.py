# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
# import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class AppProxyTestCase(ModuleTestCase):
    'Test APP Proxy module'
    module = 'app_proxy'

    def setUp(self):
        super(AppProxyTestCase, self).setUp()
        trytond.tests.test_tryton.install_module('party')
        self.app_proxy = POOL.get('app.proxy')
        self.party = POOL.get('party.party')
        self.address = POOL.get('party.address')

    def test0010party(self):
        'Create party'
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            party1, = self.party.create([{
                        'name': 'Party 1',
                        }])
            self.assert_(party1.id)
            transaction.cursor.commit()

    def test0020address(self):
        'Create address'
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            party1, = self.party.search([], limit=1)

            address, = self.address.create([{
                        'party': party1.id,
                        'street': 'St sample, 15',
                        'city': 'City',
                        }])
            transaction.cursor.commit()
            self.assert_(address.id)

    def test0030app_proxy(self):
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            json = '''[{"party.party":[[["id", "=", 1]], ["name","code"],0, ""]},{"party.address":[[["city", "=", "City"]],["street","party.name"],0,""]}]'''
            json_result = '''{"party.party": [{"code": "1", "name": "Party 1", "id": 1}], "party.address": [{"street": "St sample, 15", "id": 1, "party.name": "Party 1"}]}'''
            result = self.app_proxy.app_search(json)
            self.assertEqual(result, json_result)

            json_write = '''{"party.party":[[1,{"name":"Test write4"}],[-1,{"name":"New Party Test APP"}],[-1,{"name":"New Party Test APP 2"}]]} '''
            self.app_proxy.app_write(json_write)
            parties = self.party.search([])
            self.assertEqual(len(parties), 3)
            for party in parties:
                self.assert_(party.id)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AppProxyTestCase))
    return suite
