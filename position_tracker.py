from web3 import Web3
import json
import sys
import time
from eth_abi import decode

''' USAGE (readme for further info.)
python3 position_tracker.py <BSC_NODE_URL> <WALLET_ADDRESS> <opt:[index]>
'''

BSC_RPC_URL = sys.argv[1]
print(f"=== Network: {BSC_RPC_URL}")
    
# EVM EOA TO TRACK
WALLET_ADDRESS = sys.argv[2]
print(f"=== Wallet: {WALLET_ADDRESS}")

NFT_INDEX = "all"
if len(sys.argv) > 3:
    arg = sys.argv[3].replace("#", "")
    try:
        NFT_INDEX = [int(x) for x in arg.split(",")]
    except ValueError:
        NFT_INDEX = [arg]
    print(f"=== Target index: {NFT_INDEX} ===")

# Pancake V3 Positions NFT-V1
V3_POSITION_CA = "0x46A15B0b27311cedF172AB29E4f4766fbE7F4364"
with open("abi.json", "r") as f:
    ABI = json.load(f)

# Pancake V3 Factory
V3_FACTORY_CA = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"

# BSC Connection
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
if not w3.is_connected():
    raise Exception("❌ Connection error BSC")

# Contract init.
contract = w3.eth.contract(address=V3_POSITION_CA, abi=ABI)

# flexible var
nft_balance = 0


def get_nb_positions():
    try:
        balance = contract.functions.balanceOf(WALLET_ADDRESS).call()
        print(f"Total position owned: {balance}")
        return balance
    except Exception as e:
        print(f"Error fetching balance: {e}")
        exit()

def get_individual_index(nft_balance: int):
    arr = []
    for i in range(nft_balance):
        try:
            index = contract.functions.tokenOfOwnerByIndex(WALLET_ADDRESS, i).call()
            arr.append(index)
            print(f"    # {i + 1}: {index}")
        except Exception as e:
            print(f"Error fetching index {i} : {e}")
            exit()
    return arr

def check_liquidity_and_display(nft_index: list[int]):
    arr = []
    for index in nft_index:
        try:
            position = contract.functions.positions(index).call()
            liquidity = position[7]
            token0_name = get_token_name(position[2])
            token1_name = get_token_name(position[3])
            fees = position[4]
            if (liquidity > 0):
                arr += [index]
                pool_address = get_pool_address(position[2], position[3], position[4])
                price_ratio = get_price_from_pool_tick(pool_address)

                print(f"Liquidity #{index} -> {token0_name}/{token1_name} | 1 {token0_name} = {price_ratio} {token1_name}")
                print(f"🟢 Open: https://pancakeswap.finance/liquidity/{index}?tokenId={index}&chain=bsc")
                token0_decimals = get_token_decimals(position[2])
                token1_decimals = get_token_decimals(position[3])

                show_current_liquidity(index, position, token0_name, token1_name, token0_decimals, token1_decimals, price_ratio)
                show_waiting_rewards(index, position, token0_name, token1_name, token0_decimals, token1_decimals, price_ratio)
                
        except Exception as e:
            print(f"Error fetching position for # {index} : {e}")
            exit()
    return arr
    
def show_current_liquidity(index, position, token0_name, token1_name, token0_decimals, token1_decimals, price_ratio):
    try:
        params = [
            bytes.fromhex("0c49ccbe"+to_hex64(index)+to_hex64(position[7])+to_hex64(1)+to_hex64(1)+to_hex64(int(time.time()+ 20 * 60)))
        ]

        result = contract.functions.multicall(params).call({"from": WALLET_ADDRESS})

        decoded_results = []
        for ret_bytes in result:
            values = [int.from_bytes(ret_bytes[i:i+32], "big") for i in range(0, len(ret_bytes), 32)]
            decoded_results.append(values)

        collect_vals = decoded_results[-1]
        amount0, amount1 = collect_vals[:2]
        amount0, amount1 = amount0/(10 ** token0_decimals), amount1/(10 ** token1_decimals)

        print("  Liquidity :")
        print(f"     + {amount0} {token0_name}      ({(price_ratio*amount0):.5f} {token1_name})")
        print(f"     + {amount1} {token1_name}")


    except Exception as e:
        print(f"Error fetching the current liquidity for # {index} : {e}")
        exit()

def show_waiting_rewards(index, position, token0_name, token1_name, token0_decimals, token1_decimals, price_ratio):
    try:
        params = (
            index,  # tokenId
            WALLET_ADDRESS,  # recipient
            340282366920938463463374607431768211455,  # amount0Max
            340282366920938463463374607431768211455   # amount1Max
        )
        result = contract.functions.collect(params).call({"from": WALLET_ADDRESS})
        result[0], result[1] = result[0]/(10 ** token0_decimals), result[1]/(10 ** token1_decimals)
        print("  Unclaimed Fees :")
        print(f"    + {result[0]} {token0_name}      ({(price_ratio*result[0]):.5f} {token1_name})")
        print(f"    + {result[1]} {token1_name}")
    except Exception as e:
        print(f"Error fetching rewards for # {index} : {e}")
        exit()

def get_pool_address(token0, token1, fee):
    token0 = w3.to_checksum_address(token0)
    token1 = w3.to_checksum_address(token1)
    factory = w3.to_checksum_address(V3_FACTORY_CA)

    selector = "0x1698ee82"
    
    data = (
        selector
        + token0[2:].rjust(64, "0")
        + token1[2:].rjust(64, "0")
        + hex(fee)[2:].rjust(64, "0")
    )

    response = w3.eth.call({"to": factory, "data": data})
    
    pool_address = "0x" + response.hex()[-40:]
    return pool_address

def get_price_from_pool_tick(pool_address):
    selector = "0x3850c7bd"

    checksum_address = w3.to_checksum_address(pool_address)

    slot0_result = w3.eth.call({"to": checksum_address, "data": selector})
    
    slot0_decoded = decode(
        ["uint256", "int256", "uint256", "uint256", "uint256", "uint256", "uint256"],
        slot0_result
    )
    current_tick = slot0_decoded[1]
    is_unlocked = slot0_decoded[6] == 1

    if is_unlocked:
        price_ratio = 1.0001 ** current_tick
        return price_ratio
    else:
        return 0



# Utility func
def get_token_name(address: str) -> str:
    try:
        checksum_address = w3.to_checksum_address(address)
        data = w3.eth.call({"to": checksum_address, "data": "0x06fdde03"})
        name = w3.to_text(data)
        name = name.replace("\x00", "").replace("\n", "").replace("\r", "").strip()
        return name if name else "?Unknown?"
    except Exception as e:
        return "?Unknown?"

def get_token_decimals(address: str) -> int:
    try:
        checksum_address = w3.to_checksum_address(address)
        data = w3.eth.call({"to": checksum_address, "data": "0x313ce567"})
        decimals = int.from_bytes(data, byteorder='big')
        return decimals
    except Exception:
        print("Warning: Error to fetch the token decimal for "+address)
        return 1

def to_hex64(n: int) -> str:
    if not isinstance(n, int):
        raise TypeError("n must be an integer.")
    if n < 0:
        raise ValueError("n must be non-negative.")
    if n >= 16**64:
        raise ValueError("n is too large to fit in 64 hexadecimal characters (>= 16**64).")
    return f"{n:064x}"


if __name__ == "__main__":
    print('-'*54)
    if (NFT_INDEX=='all'):
        nft_balance = get_nb_positions()
        NFT_INDEX = get_individual_index(nft_balance)
        print('-'*54)
    check_liquidity_and_display(NFT_INDEX)
