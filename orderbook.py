from collections import defaultdict, deque  # a faster insert/pop queue


class OrderBook:
    def __init__(self):
        self.trades = deque()
        self.bids = OrderList("B")
        self.asks = OrderList("S")
        self.transcation_log = []

    def parse_order(self, order: str):
        """
        Parse order string in the format of

        SUB LO [Side] [Order ID] [Quantity] [Price]
        Submit a Limit Order with the specified Order ID, Quantity and Price.

        SUB MO [Side] [Order ID] [Quantity]
        Submit a Market Order with the specified Order ID and Quantity.

        CXL [Order ID]
        Cancel the order in the OB with the specified Order ID. If there is no order in the OB with the specified Order ID, this action should do nothing.
        """
        order_command = order.split()
        action = order_command[0]
        # log bid and ask
        self.transcation_log.append(
            f"Bid : {self.bids.order_map}, Ask : {self.asks.order_map}")

        if action == 'SUB':
            order_type, side, order_id, quantity = order_command[
                1], order_command[2], order_command[3], int(order_command[4])
            if order_type == 'LO':
                price = int(order_command[5])
                self.process_limit_order(side, order_id, quantity, price)
            elif order_type == 'MO':
                self.process_market_order(side, quantity)

        elif action == 'CXL':  # cancel order
            order_id = order_command[1]
            self.cancel_order(order_id)

    def process_limit_order(self, side, order_id, quantity, price):
        # add to txn log
        quantity_to_trade = quantity
        if side == 'B':
            while quantity_to_trade > 0 and self.asks.num_orders > 0 and price >= self.asks.min_price():
                print(self.asks.min_price())
                # print type self.asks.min_price()
                print(type(self.asks.min_price()))
                best_ask_price_order = self.asks.get_min_price_order()
                quantity_to_trade = self.process_order(
                    quantity_to_trade, best_ask_price_order)

            # when there is no more ask order, or the price is less than the ask order,
            # add the order to the bid list
            if quantity_to_trade > 0:
                print("Inserting Order into Bid List")
                self.bids.insert_order(
                    side, order_id, quantity_to_trade, price)

        elif side == 'S':
            while quantity_to_trade > 0 and self.bids.num_orders > 0 and price <= self.bids.max_price():
                best_bid_price_order = self.bids.get_max_price_order()
                quantity_to_trade = self.process_order(
                    quantity_to_trade, best_bid_price_order)
            # when there is no more bid order, or the price is greater than the bid order,
            # add the order to the ask list
            if quantity_to_trade > 0:
                print("Inserting Order into Ask List")
                self.asks.insert_order(
                    side, order_id, quantity_to_trade, price)

    def process_market_order(self, side, quantity):
        quantity_to_trade = quantity
        if side == 'B':
            while quantity_to_trade > 0 and self.asks.num_orders > 0:
                best_ask_price_order = self.asks.get_min_price_order()
                quantity_to_trade = self.process_order(
                    quantity_to_trade, best_ask_price_order)
            if quantity_to_trade > 0:
                return  # cancel order when market order is not filled

        elif side == 'S':
            while quantity_to_trade > 0 and self.bids.num_orders > 0:
                best_bid_price_order = self.bids.get_max_price_order()
                quantity_to_trade = self.process_order(
                    quantity_to_trade, best_bid_price_order)
            if quantity_to_trade > 0:
                return

    def process_order(self, quantity_to_trade, target_order):
        """ Processes the order by finding the best price and quantity to trade. """
        print("Initial : ", quantity_to_trade)

        if quantity_to_trade > 0:
            if quantity_to_trade > target_order.quantity:
                quantity_to_trade -= target_order.quantity
                target_order.quantity = 0
                self.asks.remove_order(target_order)

            elif quantity_to_trade < target_order.quantity:
                target_order.quantity -= quantity_to_trade
                quantity_to_trade = 0

        print(quantity_to_trade)
        return quantity_to_trade

    def cancel_order(self, order_id):
        # find the order id in both bid and ask, and remove it from the list
        if order_id in self.bids.order_map:
            self.bids.remove_order(order_id)
        elif order_id in self.asks.order_map:
            self.asks.remove_order(order_id)


class OrderList:
    """ Order list stores Order sorted according to price"""

    def __init__(self, side):
        self.price_map = defaultdict(list)  # Dict of price : Order object
        self.prices = PriceList()  # List of prices
        self.order_map = {}  # Dictionary containing order_id : Order object
        self.num_orders = 0  # Contains count of Orders in tree
        self.side = side  # Contains side of the order

    def get_max_price_order(self):
        if self.num_orders > 0:
            return self.price_map[self.max_price()][0]
        else:
            return None

    def get_min_price_order(self):
        if self.num_orders > 0:
            return self.price_map[self.min_price()][0]
        else:
            return None

    def max_price(self):
        return self.prices[-1] if self.num_orders > 0 else None

    def min_price(self):
        return self.prices[0] if self.num_orders > 0 else None

    def order_exists(self, order_id):
        return self.order_map.get(order_id) != None

    def insert_order(self, side, order_id, quantity, price):
        """
        Inserts an order into the order list.
        Adds to the price map, order map, price list of order list
        """
        order = Order(side, order_id, quantity, price)
        self.price_map[price].append(order)
        self.order_map[order_id] = order
        self.prices.add(price)
        self.num_orders += 1

    def update_order(self, order_id, update_quantity):
        """Update the order to given commands"""
        order = self.order_map.get(order_id)
        if order != None:
            order.quantity += update_quantity
            if order.quantity == 0:
                self.remove_order_by_id(order_id)
                return 0
            elif order.quantity < 0:
                pass

    def remove_order(self, order):
        self.remove_order_by_id(order.order_id)
        self.remove_order_by_price(order)

    def remove_order_by_id(self, order_id):
        order = self.order_map.get(order_id)
        if order != None:
            self.num_orders -= 1
            del self.order_map[order_id]

    def remove_order_by_price(self, order):
        """Removes order from prices list and price map"""
        order_price = order.price
        price_list = self.price_map.get(order_price)
        if price_list != None:
            for i in range(len(price_list)):
                if price_list[i].order_id == order.order_id:
                    del price_list[i]
                    break
            self.prices.remove(order_price)

            if len(price_list) == 0:
                del self.price_map[order_price]
            else:
                self.price_map[order_price] = price_list

    def get_orders(self):
        return [str(order) for order in self.order_map.values()]

    def __str__(self) -> str:
        # price in the format of "B : [order, order, order]"
        return f"{self.side} : {self.get_orders()}"


class Order:
    """Order class to store each bid/ask order information."""

    def __init__(self, side, order_id, quantity, price):
        self.side = side
        self.order_id = order_id
        self.quantity = quantity
        self.price = price

    @ property
    def side(self) -> str:
        return self._side

    @ property
    def order_id(self) -> int:
        return self._order_id

    @ property
    def price(self) -> int:
        return self._price

    @ property
    def quantity(self) -> int:
        return self._quantity

    @ property
    def next(self) -> 'Order':
        return self._next

    @ property
    def prev(self) -> 'Order':
        return self._prev

    @ side.setter
    def side(self, side) -> None:
        if side == 'B' or side == 'S':
            self._side = side
        else:
            raise ValueError('Invalid side')

    @ order_id.setter
    def order_id(self, order_id) -> None:
        self._order_id = order_id

    @ price.setter
    def price(self, price) -> None:
        if isinstance(price, int):
            self._price = price
        else:
            raise ValueError('Invalid price')

    @ quantity.setter
    def quantity(self, quantity) -> None:
        if isinstance(quantity, int):
            self._quantity = quantity
        else:
            raise ValueError('Invalid quantity')

    def __str__(self) -> str:
        return f'{self.quantity}@{self.price}#{self.order_id}'


class PriceList:
    """Double linked list to store prices and maintain sorted order"""

    def __init__(self):
        self.head = None
        self.tail = None
        self.num_prices = 0

    def add(self, price):
        """Inserts a price into the sorted price list"""
        if self.head == None:
            self.head = PriceNode(price)
            self.tail = self.head
        elif price <= self.head.price:
            node = PriceNode(price)
            node.next = self.head
            self.head.prev = node
            self.head = node
        elif price >= self.tail.price:
            node = PriceNode(price)
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        else:
            node = PriceNode(price)
            current = self.head
            while ((current.next is not None) and
                   (current.next.price < node.price)):
                current = current.next

            node.next = current.next
            if current.next is not None:
                node.next.prev = node
            current.next = node
            node.prev = current

        self.num_prices += 1

    def remove(self, price):
        """Remove price from the price list"""
        current = self.head
        while current != None:
            if current.price == price:
                if current.prev == None:
                    self.head = current.next
                else:
                    current.prev.next = current.next
                if current.next == None:
                    self.tail = current.prev
                else:
                    current.next.prev = current.prev
                self.num_prices -= 1
                return
            current = current.next

    def get_prices(self):
        """Returns a list of prices"""
        prices = []
        current = self.head
        while current != None:
            prices.append(current.price)
            current = current.next
        return prices

    def __str__(self) -> str:
        """Returns the string representation of the price list"""
        current = self.head
        result = ''
        while current != None:
            result += f'{current.price}'
            current = current.next
        return result


class PriceNode:
    """Node for price in price list"""

    def __init__(self, price):
        self.price = price
        self.next = None
        self.prev = None

    def __str__(self) -> str:
        return f'{self.price}'