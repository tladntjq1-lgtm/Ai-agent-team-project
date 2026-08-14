# 📄 ERD 명세서 (ERD Specification)

## 1. ERD 다이어그램 (Mermaid)

```mermaid
erDiagram
    TEAM ||--|{ USER : contains
    USER ||--o{ ISSUE : assigns
    
    TEAM {
        bigint id PK
        string team_name
        int max_members "기본값 6"
    }
    
    USER {
        bigint id PK
        string name
        string role "통합담당자, 개발자 등"
        bigint team_id FK
    }
    
    ISSUE {
        bigint id PK
        string title
        string br_id "BR 연동 식별자"
        bigint assignee_id FK
    }