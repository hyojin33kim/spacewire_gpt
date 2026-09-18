# SpaceWire Spec2RTL

ECSS-E-ST-50-12C Rev.1 기반으로 SpaceWire Golden Model, Verification Oracle, FPGA RTL을 개발하기 위한 engineering repository입니다.

## Source of Truth

- Git: requirement 해석, behavior contract, Golden Model, test, RTL, traceability의 정본
- Original specification: 변경 금지 reference
- SQLite/HTML/report: source에서 재생성되는 derived artifact

## Flow

```
Spec
  -> Semantic Model / Ontology
  -> Atomic Requirement
  -> Behavior Contract
  -> Golden Model
  -> Verification
  -> RTL Contract
  -> FPGA RTL
```

## Repository

- `spec/` : source manifest와 spec 분석 메타데이터
- `ontology/` : canonical terms/entities/relations
- `requirements/` : atomic requirements
- `contracts/` : behavior contracts
- `golden_model/` : implementation-independent reference model
- `verification/` : tests, invariants, assertions
- `rtl/` : FPGA RTL
- `traceability/` : Spec -> Contract -> Model -> Test -> RTL trace
- `generated/` : 재생성 가능한 DB/report

기존 Streamlit 연습 내용은 Git history에 남아 있으며, 이 시점부터 SpaceWire 전용 repository로 사용합니다.
