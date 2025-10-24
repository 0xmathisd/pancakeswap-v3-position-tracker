from web3 import Web3
import sys
from eth_abi import decode

# token / USDT pairs
POOL_ADDRESSES = [
    "0xaead6bd31dd66eb3a6216aaf271d0e661585b0b1",
    "0x7e58f160b5b77b8b24cd9900c09a3e730215ac47",
    "0x9d66f536b5d0d4a6086ffbef06a12c5caa9a1460",
    "0x30db6dfdb8817765797bd62316e41f5f4e431e93",
    "0x8bfb0fb037b30562fdb7be3f71440575664ab74e",
]
POOL_ADDRESSES = list(set(POOL_ADDRESSES))  # Remove duplicates

BSC_RPC_URL = sys.argv[1]
print(f"=== Network: {BSC_RPC_URL}")

web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
if not web3.is_connected():
    raise Exception("❌ Unable to connect to the node")

SLOT0_SELECTOR = "0x3850c7bd"   # slot0()
FEE_SELECTOR = "0xddca3f43"     # fee()

for pool_address in POOL_ADDRESSES:
    print('-' * 54)
    print(f"📘 Pool address: {pool_address}")

    checksum_address = Web3.to_checksum_address(pool_address)

    fee_result = web3.eth.call({"to": checksum_address, "data": FEE_SELECTOR})
    slot0_result = web3.eth.call({"to": checksum_address, "data": SLOT0_SELECTOR})

    slot0_decoded = decode(
        ["uint256", "int256", "uint256", "uint256", "uint256", "uint256", "uint256"],
        slot0_result
    )
    fee_decoded = decode(["uint24"], fee_result)

    sqrt_price_x96 = slot0_decoded[0]
    current_tick = slot0_decoded[1]
    observation_index = slot0_decoded[2]
    observation_cardinality = slot0_decoded[3]
    next_observation_cardinality = slot0_decoded[4]
    protocol_fee = slot0_decoded[5]
    is_unlocked = slot0_decoded[6] == 1
    pool_fee_percent = fee_decoded[0] / 10000

    if is_unlocked:
        price_ratio = 1.0001 ** current_tick
        print(f"🟢 Pool status: Unlocked")
        print(f"   → Tick: {current_tick}")
        print(f"   → Price (token0/token1): {price_ratio}")
        print(f"   → Fee Tier: {pool_fee_percent}%")
    else:
        print("🔴 Pool is locked")

