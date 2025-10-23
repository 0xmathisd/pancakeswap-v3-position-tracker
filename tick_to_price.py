import math

t = float(input("Tick = ").replace(",", "."))

p = 1.0001 ** t

print(f"Asset price = {p}")