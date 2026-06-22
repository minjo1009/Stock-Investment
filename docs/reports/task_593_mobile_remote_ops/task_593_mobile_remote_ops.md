# Task593 - Mobile Remote Ops

## Decision Summary

- decision_status=PRIMARY_PASS
- objective=Manage and monitor the Korean paper-trading workstation from a phone while traveling.
- remote_access_model=Tailscale private tailnet
- trader_terminal_url=http://100.90.255.9:5173/
- workstation_power_policy=HIBERNATE_FIRST
- public_port_forwarding=FORBIDDEN
- real_capital_claim=NO_GO_FOR_REAL_CAPITAL

## Quant Expert Report

The local LAN-only answer was insufficient for travel. The remote operating model now uses Tailscale to connect the phone and Korean workstation through an authenticated private tailnet.

Tailscale 1.98.2 is installed on the workstation, the service is automatic/running, and the workstation has Tailscale IP `100.90.255.9`. Trader Terminal is served on stable port `5173` using the built Vite preview server. The endpoint `http://100.90.255.9:5173/` returned HTTP 200 from the workstation.

The `TraderTerminalMobileServer` scheduled task starts the mobile server at logon and at the same wake windows used for Nasdaq paper operations. This is intentionally tied to the hibernate-first workstation policy: the phone can reach the workstation when it is awake, while hibernate remains offline by design.

No trading signal, order, risk, fill, or PnL logic changed in this task.

## No-Background Decision-Maker Report

스페인에서도 휴대폰으로 한국 PC의 모의거래 화면을 볼 수 있게 원격 운영 구조를 만들었습니다.

핵심은 Tailscale입니다. 휴대폰에 Tailscale 앱을 설치하고 같은 계정으로 로그인하면, 한국 PC가 깨어 있는 동안 `http://100.90.255.9:5173/`로 Trader Terminal에 접속할 수 있습니다.

PC가 최대절전 상태일 때는 일부러 오프라인입니다. 장 시작 전 예약 작업이 PC를 깨우면 Tailscale과 Trader Terminal 서버가 다시 살아나고, 그때 휴대폰에서 확인하면 됩니다.

## Artifact Manifest

See `artifact_manifest.csv`.
