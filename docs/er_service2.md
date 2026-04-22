```mermaid
erDiagram
    auth_user ||--o{ property_like : "da like"
    property  ||--o{ property_like : "recibe like"
    property  ||--o{ status_history : "tiene historial"
    status    ||--o{ status_history : "cataloga"

    auth_user {
        int id PK
        varchar username
        varchar email
        varchar password
        datetime date_joined
        boolean is_active
    }

    property {
        int id PK
        varchar address
        varchar city
        bigint price
        text description
        int year
    }

    status {
        int id PK
        varchar name UK
        varchar label
    }

    status_history {
        int id PK
        int property_id FK
        int status_id FK
        datetime update_date
    }

    property_like {
        int id PK
        int user_id FK
        int property_id FK
        datetime created_at
    }
```
