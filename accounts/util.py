#
#   Author(s): Huon Imberger
#   Description: Utility methods
#

def is_credit_card_valid(card_number):
    """
    Checks the validity of a credit card using the Luhn algorithm
    Source: https://en.wikipedia.org/wiki/Luhn_algorithm#Python
    :param card_number: the credit card number to check
    :return: Boolean
    """
    sum = 0
    parity = len(card_number) % 2
    for i, digit in enumerate([int(x) for x in card_number]):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        sum += digit
    return sum % 10 == 0

def is_digits(string):
    """
    Checks if a string is entirely digits (no decimals)
    :param string: The string to check
    :return: Boolean
    """
    try:
        int(string)
        return True
    except ValueError:
        return False
