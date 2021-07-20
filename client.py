from decimal import Decimal

from limit_order_book import Order, OrderStatus, LimitOrderBook, OrderUpdate, OrderSide


class Client:

    def __init__(self, name: str):
        self.name = name
        self.active_orders = set()

    def create_order(self, price: float, size: float, side: OrderSide, venue: LimitOrderBook):
        order = Order(Decimal(str(price)), Decimal(
            str(size)), side, venue, owner=self)
        venue.add_order(order)
        return order

    def cancel_order(self, order: Order):
        order.venue.remove_order(order)
        return order

    def receive_update(self, update: OrderUpdate):
        s = update.status
        if (s is OrderStatus.FILLED) or (s is OrderStatus.CANCELLED):
            self.active_orders.remove(update.order)
        elif s is OrderStatus.POSTED:
            self.active_orders.add(update.order)

    def __repr__(self):
        return self.name
