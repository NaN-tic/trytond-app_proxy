# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import app
from . import stock

def register():
    Pool.register(
        app.AppProxy,
        module='app_proxy', type_='model')
    Pool.register(
        stock.ShipmentIn,
        depends=['stock'],
        module='app_proxy', type_='model')
