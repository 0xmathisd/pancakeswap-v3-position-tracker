from web3 import Web3
import json
import sys
import time

BSC_RPC_URL = sys.argv[1]
# EVM EOA TO TRACK
WALLET_ADDRESS = sys.argv[2]

# Pancake V3 Positions NFT-V1
CONTRACT_ADDRESS = "0x46A15B0b27311cedF172AB29E4f4766fbE7F4364"
with open("abi.json", "r") as f:
    ABI = json.load(f)

# BSC Connection
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
if not w3.is_connected():
    raise Exception("❌ Connection error BSC")

# Contract init.
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# flexible var
nft_balance = 0
nft_index = []
nft_index_active = []


def get_nb_positions():
    try:
        balance = contract.functions.balanceOf(WALLET_ADDRESS).call()
        print(f"Position NFT owned: {balance}")
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

def check_liquidity(nft_index: list[int]):
    arr = []
    print("\n==================")
    print("Liquidity")
    for index in nft_index:
        try:
            position = contract.functions.positions(index).call()
            liquidity = position[7]
            token1_name = get_token_name(position[2])
            token2_name = get_token_name(position[3])
            if (liquidity > 0):
                arr += [index]
                print(f"    # {index} Pair {token1_name}/{token2_name} = {liquidity}")
                print(f"🟢 Open https://pancakeswap.finance/liquidity/{index}?tokenId={index}&chain=bsc")
                token1_decimals = get_token_decimals(position[2])
                token2_decimals = get_token_decimals(position[3])
                show_current_liquidity(index, position, token1_name, token2_name, token1_decimals, token2_decimals)
                show_waiting_rewards(index, position, token1_name, token2_name, token1_decimals, token2_decimals)
                print('--------------------')
        except Exception as e:
            print(f"Error fetching position for # {index} : {e}")
            exit()
    return arr

def show_waiting_rewards(index, position, token1_name, token2_name, token1_decimals, token2_decimals):
    try:
        params = (
            index,  # tokenId
            WALLET_ADDRESS,  # recipient
            340282366920938463463374607431768211455,  # amount0Max
            340282366920938463463374607431768211455   # amount1Max
        )
        result = contract.functions.collect(params).call({"from": WALLET_ADDRESS})
        print("Rewards :")
        print(f"    + {result[0]/(10 ** token1_decimals)} {token1_name}")
        print(f"    + {result[1]/(10 ** token2_decimals)} {token2_name}")
    except Exception as e:
        print(f"Error fetching rewards for # {index} : {e}")
        exit()

def to_hex64(n: int) -> str:
    if not isinstance(n, int):
        raise TypeError("n must be an integer.")
    if n < 0:
        raise ValueError("n must be non-negative.")
    if n >= 16**64:
        raise ValueError("n is too large to fit in 64 hexadecimal characters (>= 16**64).")
    return f"{n:064x}"

def show_current_liquidity(index, position, token1_name, token2_name, token1_decimals, token2_decimals):
    try:
        params = [
            bytes.fromhex("0c49ccbe"+to_hex64(index)+to_hex64(position[7])+to_hex64(1)+to_hex64(1)+to_hex64(int(time.time()+ 20 * 60)))
        ]

        result = contract.functions.multicall(params).call({"from": WALLET_ADDRESS})

        decoded_results = []
        for ret_bytes in result:
            # décoder tous les uint256 (32 bytes chacun)
            values = [int.from_bytes(ret_bytes[i:i+32], "big") for i in range(0, len(ret_bytes), 32)]
            decoded_results.append(values)

        # ne prendre que le dernier élément (la dernière fonction appelée)
        collect_vals = decoded_results[-1]
        amount0, amount1 = collect_vals[:2]

        print(f"Total Liquidity + Rewards :")
        print(f"     + {amount0/(10 ** token1_decimals)} {token1_name} ")
        print(f"     + {amount1/(10 ** token2_decimals)} {token2_name}")


    except Exception as e:
        print(f"Error fetching the current liquidity for # {index} : {e}")
        exit()

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

if __name__ == "__main__":
    print(f"=== Wallet: {WALLET_ADDRESS} ===")
    print(f"=== Target: {BSC_RPC_URL} ===\n")
    nft_balance = get_nb_positions()
    nft_index = get_individual_index(nft_balance)
    nft_index_active = check_liquidity(nft_index)
