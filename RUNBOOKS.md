# Rework Operational Runbooks & Incident Response Guide

This document provides step-by-step executable runbooks for system maintainers, DevOps engineers, and incident responders operating the Rework platform.

---

## Table of Contents
1. [Deployment & Rollback Runbook](#1-deployment--rollback-runbook)
2. [Unhealthy Container & Crash Recovery Runbook](#2-unhealthy-container--crash-recovery-runbook)
3. [Database Connection Exhaustion Runbook](#3-database-connection-exhaustion-runbook)
4. [Redis Outage & Queue Recovery Runbook](#4-redis-outage--queue-recovery-runbook)
5. [Stuck AI Background Jobs Runbook](#5-stuck-ai-background-jobs-runbook)
6. [Credential Rotation & Token Revocation Runbook](#6-credential-rotation--token-revocation-runbook)
7. [User-Facing Incident Communications](#7-user-facing-incident-communications)

---

## 1. Deployment & Rollback Runbook

### Deployment Procedure
1. Check CI status on target commit: `git status`
2. Pull latest release commit:
   ```bash
   git pull origin workspace
   ```
3. Run Alembic migrations:
   ```bash
   docker compose -f docker-compose.prod.yml run --rm migrate
   ```
4. Build and restart production containers:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
5. Verify system health:
   ```bash
   curl -f http://localhost:8000/health
   ```

### Emergency Rollback Procedure
1. Downgrade database schema by 1 migration step:
   ```bash
   docker compose -f docker-compose.prod.yml run --rm migrate alembic downgrade -1
   ```
2. Revert containers to previous release tag:
   ```bash
   git checkout PREVIOUS_RELEASE_TAG
   docker compose -f docker-compose.prod.yml up -d
   ```
3. Confirm rollback success:
   ```bash
   curl -f http://localhost:8000/health
   ```

---

## 2. Unhealthy Container & Crash Recovery Runbook

### Symptoms
- `GET /health` returns `503 Service Unavailable` or `status: degraded`.
- Container healthchecks failing in `docker ps`.

### Recovery Steps
1. Inspect container health status:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
2. Fetch last 200 lines of error logs for failing container:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=200 backend
   ```
3. Restart failed container service:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```
4. If crash loop persists, inspect OOM memory kills:
   ```bash
   dmesg -T | grep -i oom
   ```

---

## 3. Database Connection Exhaustion Runbook

### Symptoms
- Log errors: `psycopg2.OperationalError: FATAL: remaining connection slots are reserved`.
- High API request latency or HTTP 500 errors on database queries.

### Recovery Steps
1. Connect to PostgreSQL container:
   ```bash
   docker compose -f docker-compose.prod.yml exec db psql -U rework_user -d rework_db
   ```
2. Count active database connections per application:
   ```sql
   SELECT count(*), state, query FROM pg_stat_activity GROUP BY state, query;
   ```
3. Terminate idle/hanging connections older than 5 minutes:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '5 minutes';
   ```
4. Adjust pool sizing in `.env`:
   ```ini
   POSTGRES_MAX_OVERFLOW=20
   ```

---

## 4. Redis Outage & Queue Recovery Runbook

### Symptoms
- Real-time WebSocket multi-node message broadcasting stops.
- Background worker tasks fail to dispatch.

### Recovery Steps
1. Check Redis ping and memory consumption:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli info memory
   ```
2. Restart Redis container if unresponsive:
   ```bash
   docker compose -f docker-compose.prod.yml restart redis
   ```
3. Restart worker containers to re-establish Redis connection:
   ```bash
   docker compose -f docker-compose.prod.yml restart worker backend
   ```

---

## 5. Stuck AI Background Jobs Runbook

### Symptoms
- ARQ queue depth growing continuously.
- Vector memory extraction or document processing hung.

### Recovery Steps
1. Inspect ARQ worker logs:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=100 worker
   ```
2. Flush corrupted job queue if necessary:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli del arq:queue
   ```
3. Restart ARQ background worker pool:
   ```bash
   docker compose -f docker-compose.prod.yml restart worker
   ```

---

## 6. Credential Rotation & Token Revocation Runbook

### Symptoms
- Suspected JWT secret leak or compromised session tokens.

### Recovery Steps
1. Generate new 64-character JWT secret:
   ```bash
   openssl rand -hex 32
   ```
2. Update `JWT_SECRET` in `.env` or production environment variables.
3. Restart backend services to invalidate all outstanding JWT access tokens immediately:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend worker
   ```
4. Verify users receive `401 Unauthorized` and are prompted to re-login.

---

## 7. User-Facing Incident Communications

### Template for Incident Notification
> **Status Update: Elevated Errors / Service Degradation**
> **Impact**: Some users may experience delay sending messages or joining channels.
> **Current Status**: Our engineering team is investigating database connection pool latency.
> **Next Update**: In 30 minutes.

### Template for Resolution Notification
> **Status Update: Resolved**
> **Summary**: All systems restored to full operation as of 11:45 UTC.
> **Root Cause**: Database pool exhaustion was resolved by connection termination and pool re-configuration.
