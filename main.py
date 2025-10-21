from web3 import Web3
import json
import sys

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
                show_waiting_rewards(index, position)
        except Exception as e:
            print(f"Error fetching position for # {index} : {e}")
            exit()
        print("==================\n")
    return arr

def show_waiting_rewards(index, position):
    try:
        token1_name = get_token_name(position[2])
        token2_name = get_token_name(position[3])
        token1_decimals = get_token_decimals(position[2])
        token2_decimals = get_token_decimals(position[3])
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
    print(get_token_name("0x000Ae314E2A2172a039B26378814C252734f556A"))
    print(f"=== Wallet: {WALLET_ADDRESS} ===")
    print(f"=== Target: {BSC_RPC_URL} ===\n")
    nft_balance = get_nb_positions()
    nft_index = get_individual_index(nft_balance)
    nft_index_active = check_liquidity(nft_index)

    print("continue")
