# TASK-4163 GPT Pro Review Capture

GPT Pro was opened in Chrome with the local evidence packet and instructed not to use GitHub as current source of truth. Both attempts stalled in long Pro reasoning, but both visible partial responses converged on the same bounded design direction.

## Attempt 1 Visible Response

```text
    - paragraph: New collector code can emit recall fields after a future natural restart.
    - paragraph: "L1/L2 should support both:"
      - paragraph: inline recall fields from newly collected rows
      - paragraph: sidecar recall overlay for already collected rows
  - paragraph: This avoids forcing a risky operational restart.
  - paragraph: "L1 should admit public newswire rows through three lanes:"
  - paragraph:
  - paragraph: "Key rule:"
  - paragraph: "L2 may use recall rows only as:"
  - paragraph: "Acceptable L2 outputs:"
  - paragraph: "Unacceptable L2 outputs:"
  - paragraph: Even if a row is highly relevant, it remains non-authoritative until resolved by a separate verified entity mapping process.
  - paragraph: "For each source/month:"
  - paragraph: The actual new recall counts should be filled by the script.
  - paragraph: "Do not judge success only by maximizing recall count. The goal is:"
  - paragraph:
  - paragraph:
    - button "Pro 피드백":
    - paragraph: 무엇이든 물어보세요
  - button "Pro 확장":
```

## Attempt 2 Visible Response

```text
  - paragraph:
  - paragraph: "권장 산출물:"
  - paragraph: "또는 현재 프로젝트 관례가 월별 inventory라면:"
  - paragraph:
  - paragraph: 현재 collector 경로는 크게 바꾸지 말고, write path 마지막에 derived classification을 붙이는 구조가 안전합니다.
  - paragraph: "실패 정책:"
  - paragraph: "스크립트 이름 예시:"
  - paragraph: "필수 옵션:"
  - paragraph: "필수 동작:"
  - paragraph:
  - paragraph: "L1 candidate row에 허용되는 필드:"
  - paragraph: "L1 candidate row에 금지되는 필드:"
  - paragraph:
  - paragraph: "L2에서 허용:"
  - paragraph: "L2에서 금지:"
  - paragraph: 제공된 5개월을 최소 smoke set으로 고정합니다.
  - paragraph: "예시 headline별 기대값:"
    - button "Pro 피드백":
    - paragraph: 무엇이든 물어보세요
  - button "Pro 확장":
```

## Codex Review Use

The usable GPT Pro guidance was: preserve raw data, separate authoritative ticker mapping from recall/review admission, keep weak/unmapped candidates non-authority, and let L1/L2 consume them only as diagnostic/review candidates.
