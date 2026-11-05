# class passing in the mutable list
class Shoppingcart:
    # passing a list with a default value on the constructor will make python to point every other instance to this list in memory
    def __init__(self, items=[]):
        self.items = items

    def add_item(self, item):
        self.items.append(item)

        return self.items

# class instantiating a new list if null
class ShoppingcartUpdated:
    def __init__(self, items=None):
        if items is None:
            items = []
        self.items = items

    def add_item(self, item):
        self.items.append(item)

        return self.items

    def share_cart(self, other_cart):
        # assigning the other card to the self.items will cause Python to point to the same list in memory, it should of been self.items.copy()
        other_cart.items = self.items

        return other_cart


# test class
cart1 = Shoppingcart()
cart2 = cart1
cart1.add_item('laptop')
# if you print them, they will have the same values
print(f'Cart 1: {cart1.items}')  # Cart 1: ['laptop']
print(f'Cart 2: {cart2.items}')  # Cart 2: ['laptop']

# test class
cart3 = Shoppingcart()
cart4 = Shoppingcart()
cart3.add_item('mobile')
# if you print them, they will have the same values, although now we are creating a new instance, the list is still the same plus the items from cart 1 and 2
print(f'Cart 3: {cart3.items}')  # Cart 3: ['laptop', 'mobile']
print(f'Cart 4: {cart4.items}')  # Cart 4: ['laptop', 'mobile']

# The problem is because the list we are passing on the constructor is mutable hence Python just keep a pointer to it
cart5 = ShoppingcartUpdated()
cart6 = ShoppingcartUpdated()
cart5.add_item('mouse')
cart5.share_cart(cart6)
cart5.add_item('mic')
cart6.add_item('oculus')
# noticed that even thought we have
print(f'Cart 5: {cart5.items}')  # Cart 5: ['mouse', 'mic', 'oculus']
print(f'Cart 6: {cart6.items}')  # Cart 4: Cart 6: ['mouse', 'mic', 'oculus']