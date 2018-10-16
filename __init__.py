# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import app
from . import stock
from . import product

def register():
    Pool.register(
        app.AppProxy,
        product.Category,
        product.Product,
        stock.ShipmentIn,
        module='app_proxy', type_='model')
