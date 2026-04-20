# Architecture Patterns Reference

## Backend Patterns

### REST API (recommended for most cases)
- Stateless, cacheable, well-understood
- Use when: CRUD operations, public APIs, mobile clients
- Stack: FastAPI (Python) or Express (Node) + PostgreSQL

### Event-Driven / Async
- Decoupled services, high scalability
- Use when: high throughput, async workflows, microservices
- Stack: Kafka or RabbitMQ + worker services

### Microservices
- Independent deployment, team autonomy
- Use when: large teams, different scaling needs per service
- Warning: operational complexity — only use at scale

### Monolith-first (recommended for startups)
- Simpler to build, test, deploy
- Use when: team < 10 devs, < 1M users, time-to-market priority
- Stack: FastAPI/Django + PostgreSQL + Redis

## Database Selection
| Need | Database |
|------|----------|
| Relational data, ACID | PostgreSQL |
| Document store | MongoDB |
| Cache / sessions | Redis |
| Full-text search | Elasticsearch or pg_search |
| Time-series | TimescaleDB or InfluxDB |
| Graph data | Neo4j |

## API Design Standards
- REST: noun-based URLs (/users, /orders/{id}), HTTP verbs
- Versioning: URL prefix /v1/ or Accept header
- Auth: JWT Bearer tokens, refresh token pattern
- Rate limiting: per user per endpoint
- Pagination: cursor-based for large datasets

## Component Diagram (text format)
```
[Client] → [API Gateway / Load Balancer]
              ↓
[Auth Service] ← → [App Service] → [DB: PostgreSQL]
                         ↓                ↓
                   [Cache: Redis]   [File: S3]
                         ↓
                 [Queue: RabbitMQ]
                         ↓
                  [Worker Service]
```
