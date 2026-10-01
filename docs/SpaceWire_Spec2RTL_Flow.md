# SpaceWire Spec2RTL Design Flow

이 문서는 현재 repository 구조와 설계/검증 lifecycle의 관계를 한 장으로 정리한 것입니다.

![SpaceWire Spec2RTL Design Flow](./spacewire_spec2rtl_design_flow.svg)

## Flow

```text
spec
  -> ontology
  -> requirements
  -> contracts
  -> golden_model
  -> rtl_contract
  -> rtl
  -> verification
```

- `traceability/`: 전 단계의 evidence, review, decision, freeze, handover를 유지합니다.
- `profiles/`: feature/configuration selection을 제공합니다.
- `tools/` + `.github/`: lint, automation, CI gate를 담당합니다.
- `generated/`: source artifact에서 재생성할 수 있는 report/matrix/interface docs/diagram만 둡니다.

자세한 directory authority 및 placement rule은 repository root의 `README.md`와 `AGENTS.md`를 따릅니다.
