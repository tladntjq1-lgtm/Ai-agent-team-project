# 참교육 평가 시스템 ERD 명세서

## 1. 테이블 목록 및 설명

### 1.1 `students` (학생 정보)
- **역할:** 시스템을 이용하는 학생 계정 정보
- **컬럼:**
  - `student_id` (PK): 학생 고유 식별자
  - `name`: 학생 이름
  - `email` (UNIQUE): 이메일 주소
  - `slack_id` (UNIQUE): 슬랙 계정 ID
  - `phone`: 전화번호
  - `created_at`: 생성일자

### 1.2 `teams` (팀 정보)
- **역할:** 프로젝트 내에서 구성된 팀 정보
- **컬럼:**
  - `team_id` (PK): 팀 고유 ID
  - `project_id` (FK): 연관된 프로젝트 ID
  - `team_name`: 팀명
  - `created_at`: 생성일자

### 1.3 `team_members` (팀 멤버 매칭)
- **역할:** 학생과 팀을 연결하는 매핑 테이블
- **컬럼:**
  - `team_member_id` (PK): 매핑 ID
  - `team_id` (FK): 팀 ID
  - `student_id` (FK): 학생 ID
  - `joined_at`: 참여 일자
- **제약조건:** `UNIQUE(team_id, student_id)` - 한 학생이 동일 팀에 중복 등록 방지

### 1.4 `projects` (프로젝트)
- **역할:** 진행되는 평가 프로젝트 단위
- **컬럼:**
  - `project_id` (PK): 프로젝트 ID
  - `project_name`: 프로젝트명
  - `description`: 프로젝트 설명
  - `created_at`: 생성일자

### 1.5 `evaluation_rounds` (평가 회차)
- **역할:** 프로젝트 하위의 평가 회차 (예: 1차 평가, 2차 평가)
- **컬럼:**
  - `round_id` (PK): 회차 ID
  - `project_id` (FK): 프로젝트 ID
  - `round_number`: 회차 번호 (예: 1)
  - `status`: 진행 상태 (`READY` / `IN_PROGRESS` / `COMPLETED`)
  - `start_at` / `end_at`: 시작 및 종료일시
  - `created_at`: 생성일자

### 1.6 `evaluation_questions` (평가 문항)
- **역할:** 회차별 평가 문항 관리
- **컬럼:**
  - `question_id` (PK): 문항 ID
  - `round_id` (FK): 회차 ID
  - `question_type`: 문항 유형 (`TEAM` / `INDIVIDUAL`)
  - `question_text`: 질문 내용
  - `display_order`: 화면 정렬 순서
  - `created_at`: 생성일자

### 1.7 `team_evaluation_scores` (팀 평가 점수)
- **역할:** 다른 팀에 대한 평가 점수 저장
- **컬럼:**
  - `score_id` (PK): 점수 ID
  - `round_id` (FK): 회차 ID
  - `evaluator_student_id` (FK): 평가를 진행한 학생 ID
  - `target_team_id` (FK): 평가를 받은 팀 ID
  - `question_id` (FK): 평가 문항 ID
  - `score`: 점수 (1 ~ 5점)
  - `created_at`: 제출일시
- **제약조건:** `UNIQUE(round_id, evaluator_student_id, target_team_id, question_id)` - 동일 문항 중복 평가 방지

### 1.8 `individual_evaluation_scores` (개인 평가 점수)
- **역할:** 같은 팀 팀원에 대한 동료 평가 점수 저장
- **컬럼:**
  - `score_id` (PK): 점수 ID
  - `round_id` (FK): 회차 ID
  - `evaluator_student_id` (FK): 평가를 진행한 학생 ID
  - `target_student_id` (FK): 평가 대상 팀원 학생 ID
  - `question_id` (FK): 평가 문항 ID
  - `score`: 점수 (1 ~ 5점)
  - `created_at`: 제출일시
- **제약조건:** `UNIQUE(round_id, evaluator_student_id, target_student_id, question_id)` - 동일 문항 중복 평가 방지
- **비즈니스 로직:** 평가 대상 학생은 같은 팀 소속(`team_members.team_id`)으로만 제한

---

## 2. 주요 관계 요약 (Relationship)
- `projects` (1) ── (N) `teams`
- `teams` (1) ── (N) `team_members` ── (1) `students`
- `projects` (1) ── (N) `evaluation_rounds`
- `evaluation_rounds` (1) ── (N) `evaluation_questions`
- `evaluation_rounds` (1) ── (N) `team_evaluation_scores`
- `evaluation_rounds` (1) ── (N) `individual_evaluation_scores`