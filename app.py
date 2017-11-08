# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelSQL, ModelSingleton
from trytond.rpc import RPC
from decimal import Decimal
import datetime
import json

__all__ = ['AppProxy']
__metaclass__ = PoolMeta


class AppProxy(ModelSingleton, ModelSQL):
    "This class acts as a proxy between the web applications and Tryton"
    __name__ = 'app.proxy'

    @classmethod
    def __setup__(cls):
        super(AppProxy, cls).__setup__()
        cls._error_messages.update({
            'incorrect_json': ('The received JSON is incorrect'),
            'no_result': ('Unable to fetch required data'),
            'incorrect_send_json': ('An error occurred while creating \
                the json: %s')
            })
        cls.__rpc__.update({
            'app_search': RPC(readonly=False),
            'app_write': RPC(readonly=False),
            })

    @classmethod
    def app_search(cls, JSON):
        """
        This method will search the requested data from the JSON and
        return it to the application
        """
        parser_json = cls.check_json(JSON)
        result_data = {}
        for json_element in parser_json:
            module, = json_element.keys()
            domain, fields, offset, limit = json_element[module]
            # ID is always sent
            fields.append('id')
            result_data[module] = cls.get_data(module, domain,
                    fields, offset, limit)
        return cls.create_json(result_data)

    @classmethod
    def app_write(cls, JSON):
        """
        This method will save or write records into tryton. The JSON
        is composed of the target model, the id and the values to update/save
        In the case of the ID, an id > 0 means write and id < 0 means save.
        The created ids will be returned to the application
        """
        parser_json = cls.check_json(JSON)
        created_ids = {}
        modules = parser_json.keys()

        for module in modules:
            to_write = []
            to_create = []
            for id, values in parser_json[module]:
                if id and int(id) >= 0:
                    to_write.append((id, values))
                else:
                    to_create.append(values)
            if to_write:
                cls.write_records(module, to_write)
            if to_create:
                created_ids[module] = cls.save_records(module, to_create)

        if created_ids:
            return cls.create_json(created_ids)
        return 'AK'

    @classmethod
    def check_json(cls, JSON, load=True):
        """ Checks the format of the JSON """
        try:
            if load:
                return json.loads(JSON)
            else:
                return json.dumps(JSON)
        except ValueError:
            cls.raise_except()

    @classmethod
    def create_json(cls, result_data):
        """
        This method will create the JSON using the result_data as template
        """
        if not result_data:
            cls.raise_user_error('no_result')
        return cls.check_json(result_data, False)

    @classmethod
    def get_data(cls, module, domain, fields, offset, limit):

        ModuleSearch = Pool().get(module)
        domain = cls._construct_domain(domain)
        ffields = [x for x in fields if (x in ModuleSearch._fields.keys()
            or '.' in x)]
        models = ModuleSearch.search_read(domain, int(offset), limit or None,
            order=[], fields_names=ffields)
        for model in models:
            for key in model:
                attr = model[key]
                if (isinstance(attr, datetime.date) or
                        isinstance(attr, datetime.datetime)):
                    model[key] = attr.isoformat()
                elif isinstance(attr, Decimal):
                    model[key] = float(attr)
        return models

    @classmethod
    def write_records(cls, module, elements_to_write):
        ModuleWrite = Pool().get(module)
        to_write = []

        for id, values in elements_to_write:
            values_to_write = cls._convert_data(values)
            to_write.extend(([ModuleWrite(id)], values_to_write))
        print "to write:", to_write
        ModuleWrite.write(*to_write)

    @classmethod
    def save_records(cls, module, to_create):
        ModuleSave = Pool().get(module)
        fields = ModuleSave._fields.keys()
        for value in to_create:
            value = cls._convert_data(value, fields)
        created_ids = ModuleSave.create(to_create)
        return [element.id for element in created_ids]

    @staticmethod
    def _convert_data(data, fields=[]):
        for key in data.keys():
            if fields and key not in fields:
                del data[key]
                continue
            if isinstance(data[key], float):
                data[key] = Decimal(str(data[key]))
        return data

    @classmethod
    def raise_except(cls):
        cls.raise_user_error('incorrect_json')

    @staticmethod
    def _construct_domain(domain):
        new_domain = []
        for element in domain:
            new_domain.append(tuple(element))
        return new_domain

    @staticmethod
    def _get_date(date):
        client_date = date.split('-')
        date = datetime.date(int(client_date[0]), int(client_date[1]),
            int(client_date[2]))
        return date
