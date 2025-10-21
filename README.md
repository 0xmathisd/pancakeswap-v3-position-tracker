# PancakeSwap V3 Position Tracker

This script reads a wallet's liquidity positions on PancakeSwap V3.

## Requirements

- Python 3
- `web3` library
- `json` for ABI purposes, `sys` for argv

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install web3
```

## Usage

```bash
python3 main.py <BSC_NODE_URL> <WALLET_ADDRESS>

```
```bash
python3 main.py https://bsc-dataseed.binance.org 0xYourWalletAddress
```

## Resources

- [PancakeSwap V3 Documentation](https://developer.pancakeswap.finance/contracts/v3/pancakev3pool)
- [Nonfungible Position Manager on BscScan](https://bscscan.com/address/0x46a15b0b27311cedf172ab29e4f4766fbe7f4364)
- [Pancake v3 github repo](https://github.com/pancakeswap/pancake-v3-contracts)

## Output

```
=== Wallet: 0x45D9717F599e5284d73952d91F5FEBC9e333499b ===
=== Target: https://bsc-dataseed.binance.org ===

Position NFT owned: 3
    # 1: 4859191
    # 2: 4859317
    # 3: 4859377

==================
Liquidity
    # 4859377 Pair Flōki/Tether USD = 88225670081290462259399
🟢 Open https://pancakeswap.finance/liquidity/4859377?tokenId=4859377&chain=bsc
Total Liquidity + Rewards :
     + 848558.9673777826 Flōki
     + 5074.560332704775 Tether USD
Rewards :
    + 8615.043274687068 Flōki
    + 71.04810791889386 Tether USD
--------------------
```

## Notes

The function `show_waiting_rewards(index, position)` simulates a `collect()` call to compute pending rewards for a position, similar to the PancakeSwap frontend.  
It updates the position's fees owed before collecting tokens.

### Solidity Example

```solidity
 function collect(CollectParams calldata params)
        external
        payable
        override
        isAuthorizedForToken(params.tokenId)
        returns (uint256 amount0, uint256 amount1)
    {
        require(params.amount0Max > 0 || params.amount1Max > 0);
        // allow collecting to the nft position manager address with address 0
        address recipient = params.recipient == address(0) ? address(this) : params.recipient;

        Position storage position = _positions[params.tokenId];

        PoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];

        IPancakeV3Pool pool = IPancakeV3Pool(PoolAddress.computeAddress(deployer, poolKey));

        (uint128 tokensOwed0, uint128 tokensOwed1) = (position.tokensOwed0, position.tokensOwed1);

        // trigger an update of the position fees owed and fee growth snapshots if it has any liquidity
        if (position.liquidity > 0) {
            pool.burn(position.tickLower, position.tickUpper, 0);
            (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) =
                pool.positions(PositionKey.compute(address(this), position.tickLower, position.tickUpper));

            tokensOwed0 += uint128(
                FullMath.mulDiv(
                    feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
                    position.liquidity,
                    FixedPoint128.Q128
                )
            );
            tokensOwed1 += uint128(
                FullMath.mulDiv(
                    feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
                    position.liquidity,
                    FixedPoint128.Q128
                )
            );

            position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
        }

        // compute the arguments to give to the pool#collect method
        (uint128 amount0Collect, uint128 amount1Collect) =
            (
                params.amount0Max > tokensOwed0 ? tokensOwed0 : params.amount0Max,
                params.amount1Max > tokensOwed1 ? tokensOwed1 : params.amount1Max
            );

        // the actual amounts collected are returned
        (amount0, amount1) = pool.collect(
            recipient,
            position.tickLower,
            position.tickUpper,
            amount0Collect,
            amount1Collect
        );

        // sometimes there will be a few less wei than expected due to rounding down in core, but we just subtract the full amount expected
        // instead of the actual amount so we can burn the token
        (position.tokensOwed0, position.tokensOwed1) = (tokensOwed0 - amount0Collect, tokensOwed1 - amount1Collect);

        emit Collect(params.tokenId, recipient, amount0Collect, amount1Collect);
    }
```

## About Position Redeem

To redeem a position, use the multicall() function with the following sequence:
```
{
    "func": "multicall",
    "params": [
        [
            "0c49ccbe......",
            "fc6f7865......"
        ]
    ]
}
```

### Functions
- 0c49ccbe → decreaseLiquidity()
- fc6f7865 → collect()

#### decreaseLiquidity parameters
0c49ccbe + tokenId + liquidity + amount0Min + amount1Min + deadline

| Parameter   | Description |
|--------------|-------------|
| `tokenId`    | NFT position index. |
| `liquidity`  | Retrieved from the positions getter contract call. |
| `amount0Min` | Can be set to `1` (used only for preview calls). |
| `amount1Min` | Can be set to `1` (used only for preview calls). |
| `deadline`   | Current UNIX timestamp + 20 minutes. |