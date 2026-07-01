# Mobile Remote Ops

## Goal

The Korean trading workstation must be manageable from a phone while traveling.

## Operating Model

1. The workstation stays in hibernate outside scheduled work.
2. Windows Task Scheduler wakes the workstation before Nasdaq paper-trading windows.
3. Task588 runs the paper supervisor.
4. Task589 sends EOD Slack/report artifacts.
5. Trader Terminal starts as a local web app on port `5173`.
6. Tailscale connects the phone and workstation into the same private tailnet.
7. Tailscale Serve exposes Trader Terminal inside the private tailnet.

## Phone App Requirement

Install the Tailscale app on the phone and sign in to the same account used on the workstation.

After login, the workstation is reachable only when it is awake. During hibernate it is intentionally offline.

## Scripts

- `scripts/install_trader_terminal_mobile_task.ps1`
- `scripts/start_trader_terminal_lan.ps1`
- `scripts/configure_tailscale_trader_terminal_serve.ps1`
- `scripts/verify_power_wake_readiness.ps1`

## Important Constraint

This is not a public internet exposure. Do not use raw port forwarding. Remote access should go through Tailscale or another authenticated private tunnel.
