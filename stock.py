# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.rpc import RPC

__all__ = ['ShipmentIn']


class ShipmentIn:
    __name__ = 'stock.shipment.in'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(ShipmentIn, cls).__setup__()
        cls.__rpc__.update({
            'io_finish_shipment':
                RPC(instantiate=0, readonly=False, check_access=False),
            })

    @classmethod
    def io_finish_shipment(cls, shipments):
        done_shipments = []
        for shipment in shipments:
            moves = [x for x in shipment.inventory_moves
                        if x.state not in ('done', 'cancel')]
            if not moves:
                done_shipments.append(shipment)

        if done_shipments:
            cls.done(done_shipments)
