import math

# price = 1.0001 ** tick

p = float(input("Asset price = ").replace(",", "."))
t = math.log(p) / math.log(1.0001)
print(f"Exact tick = {t}")

s = float(input("Perf in % = ").replace(",", ".").replace("-", ""))

print(f"\nProjection +{s} %")
print(f"    price = {p+p*(s/100)}")
print(f"    tickUpper = {t+s*100}")

print("\n")
    
print(f"Projection -{s} %")
print(f"    price = {p-p*(s/100)}")
print(f"    tickLower = {t-s*100}")