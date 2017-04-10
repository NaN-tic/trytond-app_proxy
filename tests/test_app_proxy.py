# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
# import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import install_module, drop_create
from trytond.pool import Pool


class AppProxyTestCase(ModuleTestCase):
    'Test APP Proxy module'
    module = 'app_proxy'

    @classmethod
    def setUpClass(cls):
        drop_create()
        super(AppProxyTestCase, cls).setUpClass()
        install_module('party')

    @with_transaction()
    def test_app_proxy(self):
        'App Proxy'
        pool = Pool()
        Party = pool.get('party.party')
        Address = pool.get('party.address')
        AppProxy = pool.get('app.proxy')
        party1, = Party.create([{
                    'name': 'Party 1',
                    }])
        self.assert_(party1.id)

        address, = Address.create([{
                    'party': party1.id,
                    'street': 'St sample, 15',
                    'city': 'City',
                    }])
        self.assert_(address.id)

        json = '''[{"party.party":[[["id", "=", 1]], ["name","code"],0, ""]},{"party.address":[[["city", "=", "City"]],["street","party.name"],0,""]}]'''
        json_result = '''{"party.party": [{"code": "1", "name": "Party 1", "id": 1}], "party.address": [{"street": "St sample, 15", "id": 1, "party.name": "Party 1"}]}'''
        result = AppProxy.app_search(json)
        self.assertEqual(result, json_result)

        json_write = '''{"party.party":[[1,{"name":"Test write4"}],[-1,{"name":"New Party Test APP"}],[-1,{"name":"New Party Test APP 2"}]]} '''
        AppProxy.app_write(json_write)
        parties = Party.search([])
        self.assertEqual(len(parties), 3)
        for party in parties:
            self.assert_(party.id)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AppProxyTestCase))
    return suite
