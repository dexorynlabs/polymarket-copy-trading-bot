"""CLOB v2 client — EIP-712 signing, L2 HMAC auth, REST endpoints.

In dry_run mode, place_order() short-circuits and logs [DRY-RUN] WOULD-PLACE
without signing or POSTing.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import random
import secrets as _secrets
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
from eth_account import Account
from eth_account.messages import encode_typed_data


CTF_EXCHANGE_V2 = "0xE111180000d2663C0091e4f400237545B87B996B"
CHAIN_ID = 137
USDC_DECIMALS = 1_000_000

# Signature types
SIG_TYPE_EOA = 0
SIG_TYPE_POLY_PROXY = 1
SIG_TYPE_POLY_GNOSIS_SAFE = 2

# Side encoding in EIP-712 struct
SIDE_BUY = 0
SIDE_SELL = 1

CLOB_API = "https://clob.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

log = logging.getLogger("clob")


@dataclass
class OrderSpec:
    """Sized, priced order ready for CLOB submission."""
    asset_id: str            # token_id (numeric string)
    side: str                # "BUY" only — bot doesn't sell
    size: float              # shares (float, will be floored to 2 dec)
    price: float             # limit price (rounded to tick already)
    order_type: str          # "FAK" (taker) or "GTC" (maker)
    market_slug: str         # for Gamma endDate lookup post-place
    target_price: float      # original target fill price (for tick inference if needed)


@dataclass
class OrderResult:
    """Result of place_order — fields available in dry_run + real."""
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None          # "matched", "live", "unmatched", "delayed"
    taking_amount_usdc: float = 0.0       # actual filled, mikro-USDC -> USDC
    making_amount_usdc: float = 0.0
    error: Optional[str] = None
    dry_run: bool = False


# ──────────────────────────────────────────────────────────────────────────
# Math helpers (ported from Rust eip712.rs:50-70)
# ──────────────────────────────────────────────────────────────────────────


def to_usdc_units(x: float) -> int:
    """Convert USD float to mikro-USDC (×1e6) integer."""
    return int(round(x * USDC_DECIMALS))


def round_to(x: float, decimals: int) -> float:
    factor = 10 ** decimals
    return round(x * factor) / factor


def floor_to(x: float, decimals: int) -> float:
    factor = 10 ** decimals
    return int(x * factor) / factor


def get_order_amounts(side: int, size: float, price: float) -> tuple[int, int]:
    """
    Returns (maker_amount, taker_amount) in mikro-USDC units.

    Per CTF Exchange V2:
      BUY:  maker pays USDC, taker provides shares
            maker_amount = floor(size, 2) * price (rounded to 4 dec)
            taker_amount = floor(size, 2)
      SELL: maker provides shares, taker pays USDC (inverse)
    """
    if side == SIDE_BUY:
        taker = floor_to(size, 2)
        maker = round_to(taker * price, 4)
        return to_usdc_units(maker), to_usdc_units(taker)
    else:
        maker = floor_to(size, 2)
        taker = round_to(maker * price, 4)
        return to_usdc_units(maker), to_usdc_units(taker)


# ──────────────────────────────────────────────────────────────────────────
# EIP-712 v2 typed data + signature
# ──────────────────────────────────────────────────────────────────────────


def _eip712_types() -> dict:
    return {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Order": [
            {"name": "salt", "type": "uint256"},
            {"name": "maker", "type": "address"},
            {"name": "signer", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
            {"name": "makerAmount", "type": "uint256"},
            {"name": "takerAmount", "type": "uint256"},
            {"name": "side", "type": "uint8"},
            {"name": "signatureType", "type": "uint8"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "metadata", "type": "bytes32"},
            {"name": "builder", "type": "bytes32"},
        ],
    }


def _eip712_domain() -> dict:
    return {
        "name": "Polymarket CTF Exchange",
        "version": "2",
        "chainId": CHAIN_ID,
        "verifyingContract": CTF_EXCHANGE_V2,
    }


def sign_order(
    private_key: str,
    funder: str,
    token_id: str,
    price: float,
    size: float,
    is_buy: bool,
    api_key: str,
    order_type: str,
) -> dict:
    """
    Build EIP-712 v2 typed data, sign, return full body for POST /order.

    `funder` = proxy wallet address (maker on PM)
    `private_key` = signer key (may differ from funder when using Gnosis Safe proxy)
    """
    # Normalize: handle both "0x..." and "0X..." prefixes, also bare hex
    key_hex = private_key.lower().removeprefix("0x")
    acct = Account.from_key("0x" + key_hex)
    signer_address = acct.address
    maker_address = funder

    side = SIDE_BUY if is_buy else SIDE_SELL
    maker_amount, taker_amount = get_order_amounts(side, size, price)

    salt = _secrets.randbelow(2**32)
    ts_ms = int(time.time() * 1000)

    sig_type = SIG_TYPE_EOA if maker_address.lower() == signer_address.lower() else SIG_TYPE_POLY_GNOSIS_SAFE

    metadata = "0x" + "00" * 32
    builder = "0x" + "00" * 32

    message = {
        "salt": salt,
        "maker": maker_address,
        "signer": signer_address,
        "tokenId": int(token_id),
        "makerAmount": maker_amount,
        "takerAmount": taker_amount,
        "side": side,
        "signatureType": sig_type,
        "timestamp": ts_ms,
        "metadata": metadata,
        "builder": builder,
    }

    signable = encode_typed_data(
        domain_data=_eip712_domain(),
        message_types={"Order": _eip712_types()["Order"]},
        message_data=message,
    )
    # Use LocalAccount.sign_message (private key already loaded into `acct`)
    signed = acct.sign_message(signable)
    signature = "0x" + signed.signature.hex()

    side_label = "BUY" if is_buy else "SELL"

    return {
        "order": {
            "salt": salt,
            "maker": maker_address,
            "signer": signer_address,
            "tokenId": token_id,
            "makerAmount": str(maker_amount),
            "takerAmount": str(taker_amount),
            "side": side_label,
            "expiration": "0",
            "signatureType": sig_type,
            "timestamp": str(ts_ms),
            "metadata": metadata,
            "builder": builder,
            "signature": signature,
        },
        "owner": api_key,
        "orderType": order_type,
    }


# ──────────────────────────────────────────────────────────────────────────
# L2 HMAC auth headers
# ──────────────────────────────────────────────────────────────────────────


def _decode_secret(secret: str) -> bytes:
    """API secret is URL-safe base64; try URL-safe first, fall back to std."""
    pad = "=" * ((4 - len(secret) % 4) % 4)
    try:
        return base64.urlsafe_b64decode(secret + pad)
    except Exception:
        return base64.b64decode(secret + pad)


def l2_headers(
    api_key: str,
    api_secret: str,
    passphrase: str,
    address: str,
    method: str,
    path: str,
    body: str,
) -> dict:
    """L2 auth — HMAC-SHA256 of (ts + METHOD + path + body) with decoded secret."""
    ts = str(int(time.time()))
    msg = f"{ts}{method.upper()}{path}{body}".encode()
    secret_bytes = _decode_secret(api_secret)
    sig = hmac.new(secret_bytes, msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode()
    return {
        "POLY_API_KEY": api_key,
        "POLY_SIGNATURE": sig_b64,
        "POLY_TIMESTAMP": ts,
        "POLY_PASSPHRASE": passphrase,
        "POLY_ADDRESS": address,
    }


# ──────────────────────────────────────────────────────────────────────────
# Client
# ──────────────────────────────────────────────────────────────────────────


class ClobClient:
    """
    REST client for CLOB v2 + Gamma API.

    In dry_run mode, place_order() returns simulated success without signing
    or making network calls (except Gamma for endDate, which is always real).
    """

    def __init__(self, secrets: Optional[dict], dry_run: bool, session: aiohttp.ClientSession):
        self.dry_run = dry_run
        self.session = session

        if dry_run:
            self.private_key = None
            self.funder = None
            self.api_key = None
            self.api_secret = None
            self.passphrase = None
            log.info("ClobClient init: DRY-RUN — no signing")
            return

        if not secrets:
            raise RuntimeError("real mode requires polymarket: section in config")
        self.private_key = secrets["private_key"]
        self.funder = secrets["wallet_address"]
        self.api_key = secrets["api_key"]
        self.api_secret = secrets["api_secret"]
        self.passphrase = secrets["passphrase"]
        # Verify key parses (use same normalization as sign_order)
        Account.from_key("0x" + self.private_key.lower().removeprefix("0x"))
        log.info(f"ClobClient init: REAL — funder={self.funder[:10]}…")

    async def place_order(self, spec: OrderSpec) -> OrderResult:
        # NOTE: success path is intentionally silent — trader.py emits a single
        # consolidated [COPY] line that combines order spec + latencies.
        # We log only on failure ([REJECT] / [ERROR]).
        if self.dry_run:
            return OrderResult(
                success=True,
                order_id=f"dry_{spec.asset_id[:8]}_{int(time.time() * 1000)}",
                status="matched",
                taking_amount_usdc=spec.size * spec.price,
                dry_run=True,
            )

        is_buy = (spec.side == "BUY")
        body_dict = sign_order(
            private_key=self.private_key,
            funder=self.funder,
            token_id=spec.asset_id,
            price=spec.price,
            size=spec.size,
            is_buy=is_buy,
            api_key=self.api_key,
            order_type=spec.order_type,
        )
        body_str = json.dumps(body_dict)
        path = "/order"
        headers = l2_headers(
            self.api_key, self.api_secret, self.passphrase,
            self.funder, "POST", path, body_str,
        )
        headers["Content-Type"] = "application/json"

        try:
            async with self.session.post(CLOB_API + path, data=body_str, headers=headers) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    log.error(f"[REJECT] POST /order {resp.status}: {text[:200]}")
                    return OrderResult(success=False, error=f"{resp.status}: {text[:200]}")
                data = json.loads(text)

            order_id = data.get("orderID") or data.get("order_id")
            status = data.get("status", "unknown")
            taking_micro = int(data.get("takingAmount", 0) or 0)
            making_micro = int(data.get("makingAmount", 0) or 0)
            return OrderResult(
                success=True,
                order_id=order_id,
                status=status,
                taking_amount_usdc=taking_micro / USDC_DECIMALS,
                making_amount_usdc=making_micro / USDC_DECIMALS,
            )
        except asyncio.TimeoutError:
            log.error("[ERROR] POST /order timeout")
            return OrderResult(success=False, error="timeout")
        except Exception as e:
            log.error(f"[ERROR] POST /order exception: {e}")
            return OrderResult(success=False, error=str(e))

    async def fetch_market_end_date(self, slug: str) -> Optional[int]:
        """
        Returns endDate as unix ms, or None on failure.
        Used to set position expiry in PositionTracker.
        Gamma is public (no auth), separate rate-limit bucket from CLOB/Data.
        """
        url = f"{GAMMA_API}/markets?slug={slug}"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 400:
                    log.warning(f"Gamma /markets {resp.status} for slug={slug}")
                    return None
                data = await resp.json()
            markets = data if isinstance(data, list) else []
            if not markets:
                return None
            # Find exact slug match; fall back to first entry
            market = next((m for m in markets if m.get("slug") == slug), markets[0])
            end_date_str = market.get("endDate") or market.get("end_date_iso")
            if not end_date_str:
                return None
            # ISO 8601 → ms
            from datetime import datetime
            dt = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception as e:
            log.warning(f"Gamma fetch failed for {slug}: {e}")
            return None
