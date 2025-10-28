#!/usr/bin/env python3
"""
Example code to demonstrate PySlice capabilities.
Try running:
    python flowslice_poc.py example.py:25:result both
"""


def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item['price']
    return total


def apply_discount(total, discount_percent):
    """Apply discount to total."""
    discount = total * (discount_percent / 100)
    return total - discount


def process_order(items, discount=10):
    """Process an order and return final price."""
    subtotal = calculate_total(items)
    result = apply_discount(subtotal, discount)  # Line 25 - Try slicing 'result'!
    return result


if __name__ == "__main__":
    # Example usage
    cart = [
        {'name': 'Book', 'price': 20},
        {'name': 'Pen', 'price': 5},
    ]

    final_price = process_order(cart, discount=15)
    print(f"Final price: ${final_price}")

    # Try these PySlice commands:
    # python flowslice_poc.py example.py:25:result backward
    #   → Shows: result comes from apply_discount(), which depends on subtotal and discount
    #
    # python flowslice_poc.py example.py:25:result forward
    #   → Shows: result is returned and becomes final_price, then printed
    #
    # python flowslice_poc.py example.py:25:result both
    #   → Shows: Complete dataflow picture!
