# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from trytond.model import (ModelView, ModelSQL, DeactivableMixin, fields)
from trytond.rpc import RPC
from trytond.protocols.jsonrpc import JSONDecoder, JSONEncoder
from decimal import Decimal
import datetime
import json

__all__ = ['AppProxy']


class AppProxy(DeactivableMixin, ModelSQL, ModelView):
    "App Proxy between the web applications and Tryton"
    __name__ = 'app.proxy'
    name = fields.Char('Name', required=True)

    @classmethod
    def __setup__(cls):
        super(AppProxy, cls).__setup__()
        cls._error_messages.update({
            'incorrect_json': ('The received JSON is incorrect'),
            'no_result': ('Unable to fetch required data'),
            'incorrect_send_json': ('An error occurred while creating '
                'the JSON: %s')
            })
        cls.__rpc__.update({
            'app_search': RPC(readonly=False),
            'app_write': RPC(readonly=False),
            })

    @classmethod
    def dump_values(cls, value):
        return json.dumps(value, cls=JSONEncoder, separators=(',', ':'), sort_keys=True)

    @classmethod
    def app_search(cls, values):
        """
        This method will search the requested data from the JSON and
        return it to the application
        """
        parser_json = json.loads(values)
        result_data = {}
        result_data['total_count'] = {}
        for json_element in parser_json:
            model, = json_element.keys()
            domain, fields, offset, limit, order, count = json_element[model]
            fields += ['id', 'create_date', 'write_date']
            result_data[model] = cls.get_data(model, domain, fields,
                    offset, limit, order)
            result_data['total_count'][model] = (cls.get_count(model, domain)
                    if count else '')
        return cls.dump_values(result_data)

    @classmethod
    def app_write(cls, values):
        """
        This method will save or write records into tryton. The JSON
        is composed of the target model, the id and the values to update/save
        In the case of the ID, an id > 0 means write and id < 0 means save.
        The created ids will be returned to the application
        """
        parser_json = json.loads(values, object_hook=JSONDecoder())
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
            return json.dumps(created_ids)
        return 'AK'

    @classmethod
    def get_data(cls, model, domain, fields, offset, limit=None, order=[]):
        pool = Pool()
        Model = pool.get(model)

        if not order:
            order = Model._order
        domain = cls._construct_domain(domain)
        records = Model.search(domain, int(offset), limit or None, order)

        def convert_field(record, fields, parent=None):
            drecord = {}
            for field in fields:
                name = '%s.%s' % (parent, field) if parent else field

                if ':' in field:
                    ffield, _subfields = field.split(':')
                    subfields = json.loads(_subfields)
                    model_field = Model._fields.get(ffield)
                    if (model_field._type == 'one2many'
                            or model_field._type == 'many2many'):
                        subrecords = []
                        for subrecord in getattr(record, ffield):
                            subfields += ['id', 'create_date', 'write_date']
                            dsubrecord = convert_field(subrecord, subfields)
                            subrecords.append(dsubrecord)
                        drecord[ffield] = subrecords
                    elif model_field._type == 'many2one':
                        subfields += ['id', 'create_date', 'write_date']
                        dsubrecord = convert_field(getattr(record, ffield), subfields, ffield)
                        drecord.update(dsubrecord)
                elif '.' in field:
                    ffield, subfield = field.split('.')
                    subrecord = getattr(record, ffield)
                    value = getattr(subrecord, subfield) if subrecord else None
                    drecord[name] = value.id if hasattr(value, 'id') else value
                else:
                    drecord[name] = getattr(record, field) if record else None
            return drecord

        app_records = []
        for record in records:
            app_records.append(convert_field(record, fields))
        return app_records

    @classmethod
    def get_count(cls, model, domain):
        pool = Pool()
        Model = pool.get(model)

        return Model.search_count(domain)

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
