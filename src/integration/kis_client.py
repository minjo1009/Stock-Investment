"""Minimal KIS paper client for one-shot US trade flow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import error, parse, request

from app.reconciliation import map_broker_status
from integration.kis_auth_manager import KISAuthManager


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass
class KISClient:
    app_key: str
    app_secret: str
    account_number: str
    product_code: str
    environment: str
    exchange_code: str
    auth_manager: KISAuthManager

    _order_branch_by_order_id: dict[str, str] | None = None

    @classmethod
    def from_env(cls) -> "KISClient":
        client = cls(
            app_key=_required_env("KIS_APP_KEY"),
            app_secret=_required_env("KIS_APP_SECRET"),
            account_number=_required_env("KIS_ACCOUNT_NUMBER"),
            product_code=_required_env("KIS_PRODUCT_CODE"),
            environment=os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper",
            exchange_code=os.environ.get("KIS_OVERSEAS_EXCHANGE_CODE", "NASD").strip().upper() or "NASD",
            auth_manager=KISAuthManager(
                app_key=_required_env("KIS_APP_KEY"),
                app_secret=_required_env("KIS_APP_SECRET"),
                environment=os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper",
                base_url=(
                    "https://openapivts.koreainvestment.com:29443"
                    if (os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper") == "paper"
                    else "https://openapi.koreainvestment.com:9443"
                ),
            ),
        )
        client._order_branch_by_order_id = {}
        return client

    @property
    def base_url(self) -> str:
        if self.environment == "paper":
            return "https://openapivts.koreainvestment.com:29443"
        return "https://openapi.koreainvestment.com:9443"

    @property
    def quote_excd(self) -> str:
        # Price quote API uses 3-char exchange code (e.g., NAS, NYS, AMS).
        mapping = {"NASD": "NAS", "NYSE": "NYS", "AMEX": "AMS"}
        return mapping.get(self.exchange_code, self.exchange_code[:3])

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        auth_required: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "custtype": "P",
        }
        if auth_required:
            headers["authorization"] = f"Bearer {self.auth_manager.get_valid_access_token()}"
        if extra_headers:
            headers.update(extra_headers)

        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=body, method=method.upper(), headers=headers)
        try:
            with request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            body_text = ""
            try:
                body_text = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                body_text = ""
            summary = self._extract_error_summary(body_text)
            raise RuntimeError(f"KIS HTTP {exc.code} for {path}: {summary}") from exc

    @staticmethod
    def _extract_error_summary(body_text: str) -> str:
        try:
            data = json.loads(body_text) if body_text else {}
        except json.JSONDecodeError:
            return "unknown_error"
        msg_cd = str(data.get("msg_cd") or data.get("error_code") or "").strip()
        msg1 = str(data.get("msg1") or data.get("error_description") or "").strip()
        if msg_cd and msg1:
            return f"{msg_cd}: {msg1}"
        if msg_cd:
            return msg_cd
        if msg1:
            return msg1
        return "unknown_error"

    def describe_auth_state(self) -> dict[str, str | bool]:
        return self.auth_manager.describe_token_state()

    def get_current_price(self, symbol: str) -> float:
        data = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/price",
            params={"AUTH": "", "EXCD": self.quote_excd, "SYMB": symbol},
            extra_headers={"tr_id": "HHDFS00000300"},
        )
        output = data.get("output", {}) if isinstance(data.get("output"), dict) else {}
        for key in ("last", "stck_prpr", "ovrs_nmix_prpr", "clos", "base"):
            value = output.get(key)
            if value not in (None, ""):
                return float(value)
        raise RuntimeError(f"Could not parse current price for {symbol}: {data}")

    def submit_order(self, symbol: str, side: str, quantity: int, limit_price: float | None = None) -> str:
        side_upper = side.strip().upper()
        if side_upper not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if self.environment == "paper":
            tr_id = "VTTT1002U" if side_upper == "BUY" else "VTTT1001U"
        else:
            tr_id = "TTTT1002U" if side_upper == "BUY" else "TTTT1006U"

        effective_price = limit_price if limit_price is not None else self.get_current_price(symbol)
        if effective_price <= 0:
            raise ValueError("limit_price must be positive")

        payload = {
            "CANO": self.account_number,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": self.exchange_code,
            "PDNO": symbol,
            "SLL_TYPE": "" if side_upper == "BUY" else "00",
            "ORD_DVSN": os.environ.get("KIS_ORDER_DVSN", "00"),  # 00: 지정가
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": f"{effective_price:.2f}",
            "ORD_SVR_DVSN_CD": "0",
        }
        data: dict[str, Any] | None = None
        last_error: Exception | None = None
        for _ in range(3):
            try:
                data = self._request(
                    "POST",
                    "/uapi/overseas-stock/v1/trading/order",
                    payload=payload,
                    extra_headers={"tr_id": tr_id},
                )
                break
            except RuntimeError as exc:
                last_error = exc
                if "EGW00201" not in str(exc):
                    raise
                time.sleep(1)
        if data is None:
            assert last_error is not None
            raise last_error
        output = data.get("output", {}) if isinstance(data.get("output"), dict) else {}
        order_id = str(output.get("ODNO", "")).strip()
        branch_no = str(output.get("KRX_FWDG_ORD_ORGNO", "")).strip()
        if not order_id:
            raise RuntimeError(f"KIS order submit failed: {data}")
        if self._order_branch_by_order_id is not None and branch_no:
            self._order_branch_by_order_id[order_id] = branch_no
        return order_id

    def get_order_status(self, order_id: str) -> str:
        rows = self.fetch_broker_order_statuses()
        for row in rows:
            if str(row.get("order_id") or "") != order_id:
                continue
            if row.get("mapped_status") == "FILLED":
                return "FILLED"
        return "PENDING"

    def fetch_broker_open_orders(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        rows = self.fetch_broker_order_statuses(symbol=symbol)
        return [row for row in rows if row.get("mapped_status") in {"SUBMITTED", "PENDING"}]

    def fetch_broker_order_statuses(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        kst = timezone(timedelta(hours=9))
        order_date = datetime.now(kst).strftime("%Y%m%d")
        tr_id = "VTTS3035R" if self.environment == "paper" else "TTTS3035R"
        params = {
            "CANO": self.account_number,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": self.exchange_code,
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "PDNO": "" if self.environment == "paper" else os.environ.get("KIS_STATUS_PDNO", ""),
            "ORD_DT": order_date,
            "ORD_STRT_DT": order_date,
            "ORD_END_DT": order_date,
            "SLL_BUY_DVSN": "00",
            "CCLD_NCCS_DVSN": "00",
            "SORT_SQN": "DS",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        try:
            data = self._request(
                "GET",
                "/uapi/overseas-stock/v1/trading/inquire-ccnl",
                params=params,
                extra_headers={"tr_id": tr_id},
            )
        except Exception:
            return []
        rows = data.get("output1")
        if not isinstance(rows, list):
            rows = data.get("output2")
        if not isinstance(rows, list):
            rows = data.get("output")
        if not isinstance(rows, list):
            return []

        symbol_u = symbol.strip().upper() if symbol else None
        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            order_id = str(row.get("odno", "")).strip()
            if not order_id:
                continue
            broker_symbol = str(row.get("pdno") or row.get("ovrs_pdno") or "").strip().upper()
            if symbol_u is not None and broker_symbol != symbol_u:
                continue
            filled_qty = float(row.get("tot_ccld_qty", 0) or 0)
            order_qty = float(row.get("ord_qty", 0) or 0)
            raw_status = str(
                row.get("ord_stts")
                or row.get("ord_sts")
                or row.get("ord_stat")
                or row.get("ccld_nccs_dvsn_name")
                or row.get("ccld_yn")
                or ""
            ).strip()
            mapped_status = map_broker_status(raw_status)
            if mapped_status == "UNKNOWN" and order_qty > 0 and filled_qty >= order_qty:
                # Explicit fallback rule for clear completion evidence.
                mapped_status = "FILLED"
            normalized.append(
                {
                    "order_id": order_id,
                    "symbol": broker_symbol,
                    "mapped_status": mapped_status,
                    "raw_status": raw_status or "UNKNOWN",
                    "order_qty": order_qty,
                    "filled_qty": filled_qty,
                    "raw_row": row,
                }
            )
        return normalized

    def get_position_quantity(self, symbol: str) -> int:
        tr_id = "VTTS3012R" if self.environment == "paper" else "TTTS3012R"
        params = {
            "CANO": self.account_number,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": self.exchange_code,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        data = self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-balance",
            params=params,
            extra_headers={"tr_id": tr_id},
        )

        rows = data.get("output1")
        if not isinstance(rows, list):
            rows = data.get("output")
        if not isinstance(rows, list):
            return 0

        symbol_u = symbol.strip().upper()
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get("pdno") or row.get("ovrs_pdno") or "").strip().upper()
            if code != symbol_u:
                continue
            qty_raw = row.get("ovrs_cblc_qty")
            if qty_raw in (None, ""):
                qty_raw = row.get("cblc_qty")
            if qty_raw in (None, ""):
                qty_raw = row.get("hold_qty")
            try:
                return int(float(qty_raw or 0))
            except ValueError:
                return 0
        return 0
