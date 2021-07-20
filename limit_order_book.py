from __future__ import annotations

from collections import deque, namedtuple
from enum import Enum
from decimal import Decimal

from sortedcontainers import SortedDict


class OrderSide(Enum):
    BUY = 0
    SELL = 1

    @classmethod
    def opposite(cls, side: OrderSide):
        if side is cls.BUY:
            return cls.SELL
        elif side is cls.SELL:
            return cls.BUY
        else:
            raise ValueError


class OrderStatus(Enum):
    CREATED = 0
    POSTED = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELLED = 4


class Order:

    def __init__(self,
                 price: Decimal = None,
                 size: Decimal = None,
                 side: OrderSide = None,
                 venue=None,
                 owner=None):

        self.price = price
        self.size = size
        self.side = side
        self.owner = owner
        self.venue = venue
        self.status = OrderStatus.CREATED
        self.order_id = None

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price: Decimal):
        if price and price > 0:
            self._price = price
        else:
            raise ValueError(
                f'Order price must any number greater than zero. Provided {price}.')

    def __repr__(self):
        return f"<id:{self.order_id}/price:{self.price}/size:{self.size}/side:{self.side}/status:{self.status}/owner:{self.owner}>"

    def update_status(self, new_status: OrderStatus):
        old_status = self.status
        self.status = new_status
        if self.owner:
            self.owner.receive_update(
                OrderUpdate(self, new_status, old_status))

    def assign_id(self, order_id: int):
        self.order_id = order_id

    def __hash__(self):
        return self.order_id


OrderUpdate = namedtuple('OrderUpdate', ('order', 'status', 'last_status'))


class LOBUnknownOrderError(Exception):
    pass


class LimitOrderBook:

    nb_books = 0

    def __init__(self, name: str):
        self.name = name
        LimitOrderBook.nb_books += 1
        self.book_id = LimitOrderBook.nb_books
        self.bids = SortedDict()
        self.asks = SortedDict()
        self.last_order = None
        self._order_count = 0

    def _new_order_id(self):
        self._order_count += 1
        return int(f"{self.book_id}{self._order_count}")

    def add_order(self, order: Order):

        order.assign_id(self._new_order_id())
        order.update_status(OrderStatus.POSTED)

        if self._is_crossing(order):
            self._match(order)

        if order.size != 0:
            p = self._convert_price(order)
            side = self.bids if order.side is OrderSide.BUY else self.asks
            side = side[p] if p in side else side.setdefault(p, deque())
            side.append(order)

        self.last_order = order

        return True

    def remove_order(self, order: Order):
        side = self.bids if order.side is OrderSide.BUY else self.asks
        p = self._convert_price(order)
        if p in side:
            try:
                side[p].remove(order)
                if len(side[p]) == 0:
                    del side[p]
                order.update_status(OrderStatus.CANCELLED)
            except ValueError:
                raise LOBUnknownOrderError
        else:
            raise LOBUnknownOrderError
        return True

    def _is_crossing(self, order: Order):
        if order.side is OrderSide.BUY:
            if len(self.asks) > 0:
                return order.price >= self.asks.peekitem()[0]
            else:
                return False
        else:
            if len(self.bids) > 0:
                return order.price <= -self.bids.peekitem()[0]
            else:
                return False

    def _convert_price(self, order: Order):
        return order.price if order.side is OrderSide.SELL else -order.price

    def _match(self, order: Order):

        if order.side is OrderSide.BUY:
            opposite_side = self.asks
            condition = order.price.__ge__
        else:
            opposite_side = self.bids
            condition = order.price.__le__

        if len(opposite_side) == 0:
            return
        top_price, top_orders = opposite_side.peekitem()

        while condition(abs(top_price)):

            matching_order = top_orders[0]
            diff = matching_order.size - order.size

            if diff < 0:
                top_orders.popleft()
                order.size -= matching_order.size
                matching_order.size = Decimal()
                if len(top_orders) == 0:
                    del opposite_side[top_price]

                order.update_status(OrderStatus.PARTIALLY_FILLED)
                matching_order.update_status(OrderStatus.FILLED)

            elif diff > 0:
                matching_order.size -= order.size
                order.size = Decimal()

                matching_order.update_status(OrderStatus.PARTIALLY_FILLED)
                order.update_status(OrderStatus.FILLED)
                return

            else:
                top_orders.popleft()
                matching_order.size = Decimal()
                order.size = Decimal()
                if len(top_orders) == 0:
                    del opposite_side[top_price]

                matching_order.update_status(OrderStatus.FILLED)
                order.update_status(OrderStatus.FILLED)
                return

            if len(opposite_side) == 0:
                return
            top_price, top_orders = opposite_side.peekitem()

    def __repr__(self):
        bids = '\n'.join(
            [f"{abs(k)} -> {list(v)}" for k, v in self.bids.items()])
        asks = '\n'.join(
            [f"{str(k)} -> {list(v)}" for k, v in self.asks.items()])
        return f"{self.name}\n{'-'*len(self.name)}\nbids:\n{bids}\nasks:\n{asks}"
