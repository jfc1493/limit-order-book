from limit_order_book import LimitOrderBook, OrderSide
from client import Client

if __name__ == "__main__":

    # Example usage in a crypto-markets simulation setting

    # setup exchanges
    binance = LimitOrderBook('binance')
    coinbase = LimitOrderBook('coinbase')

    # create simulation agents (simulator can be background noise)
    mm = Client('market-maker')
    simulator = Client('simulator')

    # send orders
    order = mm.create_order(102, 0.7, OrderSide.SELL, binance)
    simulator.create_order(102, 0.5, OrderSide.BUY, coinbase)

    # check
    print(mm.active_orders)
    print(binance, coinbase)
