# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields
from trytond.rpc import RPC

__all__ = ['Category', 'Product']


class Category:
    __metaclass__ = PoolMeta
    __name__ = "product.category"

    @classmethod
    def __setup__(cls):
        super(Category, cls).__setup__()
        cls.__rpc__.update({
            'app_categories': RPC(readonly=False),
            })

    @classmethod
    def app_category_domain(cls, app):
        return []

    @classmethod
    def app_categories(cls, app_id, category=[]):
        AppProxy = Pool().get('app.proxy')

        app = AppProxy(app_id)

        def vals(category, childs=[]):
            return {
                'id': category.id,
                'name': category.name,
                'parent': category.parent.id if category.parent else '',
                'childs': childs,
                }

        categories = []
        for category in cls.search(cls.app_category_domain(app)):
            # second level
            second_childs = []
            for cat2 in category.childs:
                # third level
                third_childs = []
                for cat3 in cat2.childs:
                    third_childs.append(vals(cat3))
                second_childs.append(vals(cat2, third_childs))
            categories.append(vals(category, second_childs))
        return AppProxy.dump_values(categories)


class Product:
    __metaclass__ = PoolMeta
    __name__ = "product.product"

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls.__rpc__.update({
            'app_quantity': RPC(readonly=False),
            })

    @classmethod
    def app_quantity(cls, product_ids, name='quantity'):
        products = cls.browse(product_ids)
        return super(Product, cls).get_quantity(products, name)
