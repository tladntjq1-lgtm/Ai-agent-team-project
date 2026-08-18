# 참교육 평가 시스템 주요 프로그램 상세 명세서 (Program Specification)

## [PGM-05] 팀 평가 작성 및 제출
- **프로그램 ID:** PGM-05
- **연관 UI:** UI-05 (`team_eval_list.html`)
- **관련 DB 테이블:** `teams`, `evaluation_questions`, `team_evaluation_scores`
- **주요 로직:**
  1. 로그인된 학생의 소속 팀(`team_id`)을 확인하여 본인 팀을 제외한 다른 팀 목록을 로드합니다.
  2. 회차별 `TEAM` 타입의 문항을 가져와 평가 양식을 구성합니다.
  3. 1~5점 척도로 입력된 점수를 `team_evaluation_scores` 테이블에 제출 저장합니다.
  4. 제출 완료된 팀 카드는 화면에서 비활성화(`disabled`) 처리하여 중복 평가를 방지합니다.

## [PGM-11] 팀 편성 관리
- **프로그램 ID:** PGM-11
- **연관 UI:** UI-11 (`admin_team_management.html`)
- **관련 DB 테이블:** `students`, `teams`, `memberships`
- **주요 로직:**
  1. 수강생 목록 중 팀 미배정 인원을 필터링합니다.
  2. [랜덤 편성] 또는 [균형 편성] 실행 시 알고리즘에 따라 팀원 조합을 자동 생성합니다.
  3. 관리자의 드래그/이동 액션에 맞춰 실시간으로 임시 팀 구성을 변경합니다.
  4. [팀 편성 확정] 처리 시 DB의 회원 소속 팀 정보를 일괄 업데이트합니다.

## [PGM-14] 결과 집계 및 석차 산출
- **프로그램 ID:** PGM-14
- **연관 UI:** UI-14 (`admin_result_management.html`)
- **관련 DB 테이블:** `team_evaluation_scores`, `individual_evaluation_scores`, `evaluation_results`
- **주요 로직:**
  1. 회차 상태가 `COMPLETED`로 변경되면 자동/수동 점수 산출을 실행합니다.
  2. 공식: `최종 점수 = (팀 점수 × 0.4) + (개인 점수 × 0.6)`
  3. 점수를 기준으로 개인별/팀별 석차를 자동 부여합니다.
  4. [결과 공개] 설정 시 학생 리포트 화면(`PGM-07`)으로 성적 데이터를 유출 허용합니다.