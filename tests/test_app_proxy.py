# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest
import json
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class AppProxyTestCase(ModuleTestCase):
    'Test App Proxy module'
    module = 'app_proxy'

    def setUp(self):
        super(AppProxyTestCase, self).setUp()
        trytond.tests.test_tryton.activate_module('party')

    @with_transaction()
    def test_party(self):
        'Create Party data'
        pool = Pool()
        Party = pool.get('party.party')
        Address = pool.get('party.address')
        ContactMechanism = pool.get('party.contact_mechanism')
        Country = pool.get('country.country')
        Subdivision = pool.get('country.subdivision')
        AppProxy = pool.get('app.proxy')
        Cron = pool.get('ir.cron')

        # Create Party Data
        country = Country(name='Country')
        country.save()
        subdivision = Subdivision(
            name='Subdivision', country=country, code='SUB', type='area')
        subdivision.save()
        subdivision2 = Subdivision(
            name='Subdivision 2', country=country, code='SUB2', type='area')
        subdivision2.save()

        party1, = Party.create([{
                    'name': 'Party 1',
                    }])
        Address.create([{
                    'sequence': 1,
                    'party': party1.id,
                    'city': 'Barcelona',
                    'subdivision': subdivision.id,
                    'country': country.id,
                    }])
        ContactMechanism.create([{
                    'party': party1.id,
                    'type': 'phone',
                    'value': '+442083661177',
                    }])
        ContactMechanism.create([{
                    'party': party1.id,
                    'type': 'email',
                    'value': 'name@example.com',
                    }])

        # Test APP Proxy Search
        model = 'party.party'
        domain = [['id', '=', 1]]
        fields = ['code', 'name', 'tax_identifier.code', 'create_date',
          'addresses:["sequence", "name", "street", "zip", "city", "country.name", "subdivision.name"]',
          'contact_mechanisms:["type", "value"]']
        offset = 0
        limit = ''
        order = []
        count = True
        # Test party.party
        json_constructor = []
        json_constructor.append({model: [domain, fields, offset, limit, order, count]})
        result = json.loads(AppProxy.app_search(json.dumps(json_constructor)))
        self.assertEqual(result['party.party'][0]['code'], '1')
        self.assertEqual(result['party.party'][0]['create_date']['__class__'], 'datetime')
        self.assertEqual(len(result['party.party'][0]['addresses']), 1)
        self.assertEqual(result['party.party'][0]['addresses'][0]['country.name'], 'Country')

        # Test party.party + party.address
        json_constructor = []
        json_constructor.append({model: [domain, fields, offset, limit, order, count]})
        model = 'party.address'
        domain = [['party', '=', 1]]
        fields = ['name', 'country.name', 'city', 'create_date']
        count = False
        json_constructor.append({model: [domain, fields, offset, limit, order, count]})
        result = json.loads(AppProxy.app_search(json.dumps(json_constructor)))
        self.assertEqual(len(result.keys()), 3)

        # Test APP Proxy Write
        json_constructor = {}
        model = 'party.party'
        to_save = []
        to_save.append([1, {"name":"Party Proxy"}])
        to_save.append([-1, {"name":"Party Proxy1"}])
        to_save.append([-1, {"name":"Party Proxy2"}])
        json_constructor[model] = to_save

        model = 'party.address'
        to_save = []
        to_save.append([1, {"name":"Address Proxy", "subdivision": 2}])
        to_save.append([-1, {"name":"Address Proxy1", "party": 2}])
        json_constructor[model] = to_save

        result = json.loads(AppProxy.app_write(json.dumps(json_constructor)))
        self.assertEqual(len(result['party.party']), 2)
        self.assertEqual(Party(1).name, 'Party Proxy')
        self.assertEqual(len(result['party.address']), 1)
        self.assertEqual(Address(1).subdivision.name, 'Subdivision 2')

        json_constructor = {}
        model = 'ir.cron'
        to_save = []
        to_save.append([1, {"next_call": {
            '__class__': 'datetime', 'hour': 00, 'month': 1, 'second': 00,
            'microsecond': 0, 'year': 1977, 'day': 01, 'minute': 00}
            }])
        json_constructor[model] = to_save
        result = AppProxy.app_write(json.dumps(json_constructor))
        self.assertEqual(Cron(1).next_call.year, 1977)

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AppProxyTestCase))
    return suite
