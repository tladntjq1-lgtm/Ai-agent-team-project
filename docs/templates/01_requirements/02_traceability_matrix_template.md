# 🗺️ 요구사항 추적표 (Traceability Matrix)

기획 단계에서 정의된 **비즈니스 규칙(BR)**이 실제 어떤 **데이터(Model)** 및 **프로그램(Program)**과 연결되어 구현되는지 추적 관리합니다.

---

## 📊 BR - 데이터 - 프로그램 매핑 추적표

| BR ID | 요구사항명 | 주요 사용자 | 관련 데이터 (Models) | 관련 프로그램/화면 (Views) | 검증 상태 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BR-01** | 자신의 팀 평가 금지 | 학생 | `Student`, `EvaluationRound`, `Team`, `TeamMember`, `TeamEvaluation` | • PG-02 팀 평가 대상 목록<br>• PG-03 팀 평가 입력 | ⏳ 대기 |
| **BR-04** | 자기 자신 개인평가 금지 및 팀원 전용 | 학생 | `Student`, `EvaluationRound`, `Team`, `TeamMember`, `PeerEvaluation` | • PG-04 동료 평가 대상 목록<br>• PG-05 동료 평가 입력 | ⏳ 대기 |
| **BR-05** | 동일 회차 중복 평가 금지 | 학생 | `Student`, `EvaluationRound`, `TeamEvaluation`, `PeerEvaluation` | • PG-03 팀 평가 입력<br>• PG-05 동료 평가 입력 | ⏳ 대기 |

---

## 💡 관리 가이드 (통합 담당자용)

1. **상태 관리**:
   - ⏳ **대기**: 요구사항 분석 완료, 개발 미진행
   - 🚧 **진행중**: 모델 및 프로그램 개발 진행 중
   - ✅ **완료**: 본인 검증(DoD) 완료 및 테스트 통과
2. **이슈 연관**: 개발 진행 시 각 BR ID를 GitHub Issue의 구현 목표로 연결하여 관리합니다.