# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
import app


def register():
    Pool.register(
        app.AppProxy,
        module='app_proxy', type_='model')
