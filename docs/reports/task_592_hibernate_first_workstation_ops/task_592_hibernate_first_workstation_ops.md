# Task592 - Hibernate First Workstation Ops

## Decision Summary

- decision_status=PRIMARY_PASS
- objective=Keep the trading workstation in hibernate rather than full shutdown, wake on schedule, then run the Nasdaq paper supervisor.
- power_policy=HIBERNATE_FIRST_NO_SHUTDOWN
- scheduled_task=ForeignStockQuantPaperWake
- scheduled_task_power_action=Hibernate
- execution_behavior_changed=POWER_POLICY_ONLY
- real_capital_claim=NO_GO_FOR_REAL_CAPITAL

## Quant Expert Report

The workstation operating policy is now hibernate-first. Task588/Task589 supervisor scripts no longer expose shutdown as a normal installer option, and the runtime runner converts any legacy `Shutdown` argument into hibernate instead of issuing `shutdown.exe /s`.

This matters operationally because Windows Task Scheduler `WakeToRun` is reliable for sleep/hibernate wake paths, while full shutdown wake depends on BIOS/UEFI RTC or external Wake-on-LAN. The project should therefore avoid full shutdown as the normal trading workstation state.

The registered scheduled task `ForeignStockQuantPaperWake` was reinstalled with `PowerActionAfterEod=Hibernate`, two local wake windows for US daylight/standard time, and `WakeToRun=True`.

No trading signal, order, risk, fill, or PnL logic changed in this task.

## No-Background Decision-Maker Report

컴퓨터는 꺼지는 방식이 아니라 최대절전 상태를 기본으로 유지하도록 정리했습니다.

장마감 후 EOD 리포트가 끝나면 shutdown이 아니라 hibernate로 들어가고, 다음 장 시작 전 Windows 예약 작업이 깨워서 Task588 모의거래 supervisor를 다시 실행합니다.

BIOS RTC 시간 입력이 완성되지 않아도 이 운영 방식은 성립합니다. 단, 완전 종료 상태에서 자동 부팅까지 보장하려면 BIOS RTC 또는 외부 Wake-on-LAN은 별도 검증이 필요합니다.

## Artifact Manifest

See `artifact_manifest.csv`.
