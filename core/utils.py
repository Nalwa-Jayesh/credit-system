from math import pow


def calculate_emi(principal, rate, tenure):
    r = rate / (12 * 100)
    emi = principal * r * pow(1 + r, tenure) / (pow(1 + r, tenure) - 1)
    return round(emi, 2)
