# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from trytond.model import ModelSingleton
from trytond.rpc import RPC
from decimal import Decimal
import datetime
import json

__all__ = ['AppProxy']


class AppProxy(ModelSingleton):
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
            model, = json_element.keys()
            domain, fields, offset, limit, order = json_element[model]
            # ID is always sent
            fields.append('id')
            result_data[model] = cls.get_data(model, domain, fields,
                                    offset, limit, order)
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
        models = parser_json.keys()

        for model in models:
            to_write = []
            to_create = []
            for id, values in parser_json[model]:
                if id and int(id) >= 0:
                    to_write.append((id, values))
                else:
                    to_create.append(values)
            if to_write:
                cls.write_records(model, to_write)
            if to_create:
                created_ids[model] = cls.save_records(model, to_create)

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
    def get_data(cls, model, domain, fields, offset, limit, order=[]):
        Model = Pool().get(model)

        domain = cls._construct_domain(domain)
        ffields = [x for x in fields if (x in Model._fields.keys()
            or '.' in x)]

        if not order:
            order = Model._order
        models = Model.search_read(domain, int(offset), limit or None,
            order, fields_names=ffields)
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
    def write_records(cls, model, elements_to_write):
        Model = Pool().get(model)

        to_write = []
        fields = Model._fields.keys()
        for id, values in elements_to_write:
            values_to_write = cls._convert_data(values, fields)
            to_write.extend(([Model(id)], values_to_write))
        Model.write(*to_write)

    @classmethod
    def save_records(cls, model, to_create):
        Model = Pool().get(model)

        fields = Model._fields.keys()
        for value in to_create:
            value = cls._convert_data(value, fields)
        created_ids = Model.create(to_create)
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
