"""Minimal KIS paper client for one-shot US trade flow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import error, parse, request
from zoneinfo import ZoneInfo

try:
    from src.app.reconciliation import map_broker_status
    from src.integration.kis_auth_manager import KISAuthManager
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from app.reconciliation import map_broker_status
    from integration.kis_auth_manager import KISAuthManager


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_order_id(value: Any) -> str:
    text = str(value or "").strip()
    return text.zfill(10) if text.isdigit() else text


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
    _order_meta_by_order_id: dict[str, dict[str, Any]] | None = None

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
        client._order_meta_by_order_id = {}
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

    @property
    def cancel_tr_id(self) -> str:
        if self.environment == "paper":
            return os.environ.get("KIS_CANCEL_TR_ID", "VTTT1004U").strip() or "VTTT1004U"
        return os.environ.get("KIS_CANCEL_TR_ID", "TTTT1004U").strip() or "TTTT1004U"

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
        price, _ = self.get_current_price_with_response(symbol)
        return price

    def get_current_price_with_response(self, symbol: str) -> tuple[float, dict[str, Any]]:
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
                return float(value), data
        raise RuntimeError(f"Could not parse current price for {symbol}: {data}")

    def supports_client_order_id(self) -> bool:
        return False

    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: float | None = None,
        *,
        idempotency_key: str | None = None,
        broker_client_order_id: str | None = None,
        reconciliation_before_retry_required: bool = True,
    ) -> str:
        order_id, _ = self.submit_order_with_response(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=limit_price,
            idempotency_key=idempotency_key,
            broker_client_order_id=broker_client_order_id,
            reconciliation_before_retry_required=reconciliation_before_retry_required,
        )
        return order_id

    def submit_order_with_response(
        self,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: float | None = None,
        *,
        idempotency_key: str | None = None,
        broker_client_order_id: str | None = None,
        reconciliation_before_retry_required: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        side_upper = side.strip().upper()
        if side_upper not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        normalized_idempotency_key = str(idempotency_key or "").strip()
        normalized_broker_client_order_id = str(broker_client_order_id or "").strip()
        if normalized_broker_client_order_id and not self.supports_client_order_id():
            raise RuntimeError("KIS_CLIENT_ORDER_ID_UNSUPPORTED")
        if normalized_idempotency_key and not self.supports_client_order_id() and not reconciliation_before_retry_required:
            raise RuntimeError("KIS_IDEMPOTENCY_REQUIRES_RECONCILIATION_BEFORE_RETRY")

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
        if normalized_idempotency_key:
            data = dict(data)
            data["_local_idempotency_key"] = normalized_idempotency_key
            data["_broker_client_order_id_supported"] = self.supports_client_order_id()
            data["_reconciliation_before_retry_required"] = reconciliation_before_retry_required
        if self._order_branch_by_order_id is not None and branch_no:
            self._order_branch_by_order_id[order_id] = branch_no
        if self._order_meta_by_order_id is not None:
            self._order_meta_by_order_id[order_id] = {
                "symbol": symbol.strip().upper(),
                "qty": int(quantity),
                "price": float(effective_price),
                "order_type": os.environ.get("KIS_ORDER_DVSN", "00"),
                "side": side_upper,
            }
        return order_id, data

    def cancel_order(
        self,
        order_id: str,
        account: str | None = None,
        symbol: str | None = None,
        qty: float | int | None = None,
        price: float | None = None,
        order_type: str | None = None,
    ) -> dict[str, Any]:
        order_id_norm = str(order_id).strip()
        if not order_id_norm:
            raise ValueError("order_id is required")
        known_meta = (self._order_meta_by_order_id or {}).get(order_id_norm, {})
        known_branch = (self._order_branch_by_order_id or {}).get(order_id_norm, "")
        payload = {
            "CANO": (account or self.account_number).strip(),
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": self.exchange_code,
            "PDNO": (symbol or known_meta.get("symbol") or "").strip().upper(),
            "ORD_QTY": str(int(float(qty if qty is not None else known_meta.get("qty") or 0))),
            "OVRS_ORD_UNPR": f"{float(price if price is not None else known_meta.get('price') or 0.0):.2f}",
            "ORD_SVR_DVSN_CD": "0",
            "RVSE_CNCL_DVSN_CD": "02",  # 01: revise, 02: cancel
            "ORGN_ODNO": order_id_norm,
            "ORD_GNO_BRNO": known_branch,
            "ORD_DVSN": (order_type or known_meta.get("order_type") or "00").strip(),
        }
        print(f"[CANCEL_API_REQUEST] order_id={order_id_norm}")
        data = self._request(
            "POST",
            "/uapi/overseas-stock/v1/trading/order-rvsecncl",
            payload=payload,
            extra_headers={"tr_id": self.cancel_tr_id},
        )
        output = data.get("output", {}) if isinstance(data.get("output"), dict) else {}
        raw_status = str(data.get("msg_cd") or output.get("ord_stts") or output.get("ord_sts") or "UNKNOWN")
        broker_status = map_broker_status(raw_status)
        success = str(data.get("rt_cd") or "").strip() == "0"
        if success and broker_status == "UNKNOWN":
            broker_status = "CANCELLED"
        print(
            f"[CANCEL_API_RESPONSE] order_id={order_id_norm} success={success} "
            f"broker_status={broker_status}"
        )
        return {"success": success, "broker_status": broker_status, "raw_response": data}

    def get_order_snapshot(self, order_id: str, *, symbol: str | None = None) -> dict[str, Any]:
        target_order_id = _normalize_order_id(order_id)
        for row in self.fetch_broker_order_statuses(symbol=symbol):
            if _normalize_order_id(row.get("order_id")) == target_order_id:
                return row
        return {
            "order_id": str(order_id),
            "symbol": (symbol or "").strip().upper(),
            "mapped_status": "UNKNOWN",
            "raw_status": "ORDER_NOT_FOUND",
            "order_qty": 0.0,
            "filled_qty": 0.0,
            "raw_row": {},
        }

    def get_order_status(self, order_id: str) -> str:
        row = self.get_order_snapshot(order_id)
        status = str(row.get("mapped_status") or "UNKNOWN")
        if status == "UNKNOWN":
            return "PENDING"
        return status

    def get_fills(self, order_id: str, *, symbol: str | None = None) -> list[dict[str, Any]]:
        row = self.get_order_snapshot(order_id, symbol=symbol)
        filled_qty = float(row.get("filled_qty") or 0.0)
        if filled_qty <= 0:
            return []
        raw_row = row.get("raw_row") if isinstance(row.get("raw_row"), dict) else {}
        fill_price = None
        for key in ("avg_ccld_unpr", "ccld_unpr", "ft_ccld_unpr3", "ovrs_ccld_unpr"):
            value = raw_row.get(key) if isinstance(raw_row, dict) else None
            if value not in (None, ""):
                try:
                    fill_price = float(value)
                    break
                except Exception:
                    fill_price = None
        filled_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [
            {
                "order_id": str(order_id),
                "symbol": str(row.get("symbol") or symbol or "").strip().upper(),
                "filled_qty": filled_qty,
                "fill_price": fill_price,
                "filled_at": filled_at,
                "raw_status": str(row.get("raw_status") or ""),
                "mapped_status": str(row.get("mapped_status") or "UNKNOWN"),
            }
        ]

    def fetch_broker_open_orders(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        rows = self.fetch_broker_order_statuses(symbol=symbol)
        return [row for row in rows if row.get("mapped_status") in {"SUBMITTED", "PENDING"}]

    def fetch_broker_order_statuses(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        rows = self.fetch_broker_unfilled_orders(symbol=symbol)
        rows.extend(self.fetch_broker_filled_or_order_history(symbol=symbol))
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for row in rows:
            key = (str(row.get("source") or ""), str(row.get("order_id") or ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    def fetch_broker_unfilled_orders(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        tr_id = "VTTS3018R" if self.environment == "paper" else "TTTS3018R"
        params = {
            "CANO": self.account_number,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": self.exchange_code,
            "SORT_SQN": "DS",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        try:
            data = self._request(
                "GET",
                "/uapi/overseas-stock/v1/trading/inquire-nccs",
                params=params,
                extra_headers={"tr_id": tr_id},
            )
        except Exception:
            return []
        rows = data.get("output")
        if not isinstance(rows, list):
            return []
        symbol_u = symbol.strip().upper() if symbol else None
        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            order_id = _normalize_order_id(row.get("odno"))
            if not order_id:
                continue
            broker_symbol = str(row.get("pdno") or row.get("ovrs_pdno") or "").strip().upper()
            if symbol_u is not None and broker_symbol != symbol_u:
                continue
            order_qty = _safe_float(row.get("ft_ord_qty", row.get("ord_qty", 0)), 0.0)
            filled_qty = _safe_float(row.get("ft_ccld_qty", row.get("tot_ccld_qty", 0)), 0.0)
            pending_qty = _safe_float(row.get("nccs_qty", 0), 0.0)
            raw_status = str(row.get("prcs_stat_name") or row.get("rjct_rson_name") or "UNFILLED").strip()
            mapped_status = "PENDING" if pending_qty > 0 or order_qty > filled_qty else map_broker_status(raw_status)
            normalized.append(
                {
                    "source": "inquire_nccs",
                    "order_id": order_id,
                    "symbol": broker_symbol,
                    "mapped_status": mapped_status,
                    "raw_status": raw_status or "UNFILLED",
                    "order_qty": order_qty,
                    "filled_qty": filled_qty,
                    "raw_row": row,
                }
            )
        return normalized

    def fetch_broker_filled_or_order_history(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        kst = timezone(timedelta(hours=9))
        kst_date = datetime.now(kst).strftime("%Y%m%d")
        et_date = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d")
        order_dates = list(dict.fromkeys([et_date, kst_date]))
        tr_id = "VTTS3035R" if self.environment == "paper" else "TTTS3035R"
        symbol_u = symbol.strip().upper() if symbol else None
        normalized: list[dict[str, Any]] = []
        for order_date in order_dates:
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
                continue
            rows = data.get("output1")
            if not isinstance(rows, list):
                rows = data.get("output2")
            if not isinstance(rows, list):
                rows = data.get("output")
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                order_id = _normalize_order_id(row.get("odno"))
                if not order_id:
                    continue
                broker_symbol = str(row.get("pdno") or row.get("ovrs_pdno") or "").strip().upper()
                if symbol_u is not None and broker_symbol != symbol_u:
                    continue
                filled_qty = _safe_float(row.get("tot_ccld_qty", row.get("ft_ccld_qty", 0)), 0.0)
                order_qty = _safe_float(row.get("ord_qty", row.get("ft_ord_qty", 0)), 0.0)
                raw_status = str(
                    row.get("ord_stts")
                    or row.get("ord_sts")
                    or row.get("ord_stat")
                    or row.get("ccld_nccs_dvsn_name")
                    or row.get("prcs_stat_name")
                    or row.get("ccld_yn")
                    or ""
                ).strip()
                mapped_status = map_broker_status(raw_status)
                if mapped_status == "UNKNOWN" and order_qty > 0 and filled_qty >= order_qty:
                    # Explicit fallback rule for clear completion evidence.
                    mapped_status = "FILLED"
                normalized.append(
                    {
                        "source": "inquire_ccnl",
                        "order_id": order_id,
                        "symbol": broker_symbol,
                        "mapped_status": mapped_status,
                        "raw_status": raw_status or "UNKNOWN",
                        "order_qty": order_qty,
                        "filled_qty": filled_qty,
                        "raw_row": row,
                    }
                )
            if len(order_dates) > 1:
                time.sleep(0.35)
        deduped: dict[str, dict[str, Any]] = {}
        for row in normalized:
            deduped[str(row.get("order_id") or "")] = row
        return list(deduped.values())

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
