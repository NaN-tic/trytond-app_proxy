# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.app_proxy.tests.test_app_proxy import suite
except ImportError:
    from .test_app_proxy import suite

__all__ = ['suite']
