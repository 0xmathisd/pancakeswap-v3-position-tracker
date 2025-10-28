from web3 import Web3
import sys
from eth_abi import decode

# token / USDT pairs
POOL_ADDRESSES = [
    "0x7e58f160b5b77b8b24cd9900c09a3e730215ac47"
]
POOL_ADDRESSES = list(set(POOL_ADDRESSES))  # Remove duplicates

BSC_RPC_URL = sys.argv[1]
print(f"=== Network: {BSC_RPC_URL}")

web3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
if not web3.is_connected():
    raise Exception("❌ Unable to connect to the node")

SLOT0_SELECTOR = "0x3850c7bd"   # slot0()
FEE_SELECTOR = "0xddca3f43"     # fee()

pool_values = {addr: 0.0 for addr in POOL_ADDRESSES}
while 1:
    for pool_address in POOL_ADDRESSES:
        checksum_address = Web3.to_checksum_address(pool_address)

        if (pool_values[pool_address] == 0.0):
            fee_result = web3.eth.call({"to": checksum_address, "data": FEE_SELECTOR})
            fee_decoded = decode(["uint24"], fee_result)
            pool_values[pool_address] = fee_decoded[0] / 10000
            
        slot0_result = web3.eth.call({"to": checksum_address, "data": SLOT0_SELECTOR})

        slot0_decoded = decode(
            ["uint256", "int256", "uint256", "uint256", "uint256", "uint256", "uint256"],
            slot0_result
        )

        sqrt_price_x96 = slot0_decoded[0]
        current_tick = slot0_decoded[1]
        observation_index = slot0_decoded[2]
        observation_cardinality = slot0_decoded[3]
        next_observation_cardinality = slot0_decoded[4]
        protocol_fee = slot0_decoded[5]
        is_unlocked = slot0_decoded[6] == 1
        

        if is_unlocked:
            print('-' * 54)
            print(f"📘 Pool address: {pool_address}")
            price_ratio = 1.0001 ** current_tick
            print(f"   → Price: {price_ratio:.5}")
            print(f"   → Achat: {price_ratio*(1+pool_values[pool_address]/100):.5}")

