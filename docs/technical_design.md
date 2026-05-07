# Technical Architecture & Design Document

This document outlines the technical stack, architectural patterns, and security models used in the YourBestPath Fiduciary Platform.

## 1. Technical Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 18 (Vite) | High-performance HMR and modern component architecture. |
| **Routing** | TanStack Router | Type-safe routing with built-in code splitting and loader support. |
| **Styling** | Vanilla CSS + Tailwind | Premium, custom-tailored aesthetics with utility-first speed. |
| **Icons** | Lucide React | Consistent, lightweight vector iconography. |
| **Backend** | FastAPI (Python 3.12+) | High-performance asynchronous API framework with Pydantic validation. |
| **Database** | ArcticDB (LMDB engine) | High-performance time-series and document store for financial data. |
| **Auth/Security** | Fernet (AES-128) + SHA-256 | Institutional-grade encryption for PII and one-way hashing for passwords. |
| **Analytics** | Pandas + NumPy | Industry-standard libraries for quantitative portfolio optimization. |
| **Market Data** | Yahoo Finance (yfinance) | Real-time and historical price retrieval for valuation. |

---

## 2. Authentication & Security Model

The system operates on a **Zero-Knowledge-Adjacent** principle where PII is never stored in plain text.

### 2.1 Password Security
- **Algorithm**: SHA-256 Hashing.
- **Salting**: Global salt derived from the `MASTER_ENCRYPTION_KEY` environment variable.
- **Storage**: Only the final hexadecimal hash is stored in ArcticDB.

### 2.2 Data Encryption (PII)
- **Technology**: Fernet Symmetric Encryption (AES-128 in CBC mode with HMAC for integrity).
- **Scope**: User names, emails, and sensitive financial metadata.
- **Key Management**: Keys are derived from the `MASTER_ENCRYPTION_KEY`. If the key is missing, a temporary volatile key is used (warning issued).

### 2.3 Anonymous Storage
- **Storage Keys**: User records are indexed by a `user_key` (SHA-256 hash of the email), ensuring no PII is visible in the database's internal symbol lists.

---

## 3. Data Strategy & Caching

### 3.1 Persistence (ArcticDB)
- **Libraries**:
    - `user_profiles`: Encrypted credentials and settings.
    - `user_goals`: Life goals, risk profiles, and timelines.
    - `user_portfolios`: Raw holdings (Symbol, Quantity, Avg Price).
    - `market_data`: Cached historical price series.
    - `audit_log`: Immutable log of fiduciary advice and data quality events.

### 3.2 Caching Mechanisms
- **PFRA Cache**: The Passive Fund Research Assistant (PFRA) caches scheme databases and filtered universes to minimize external API hits.
- **Historical Cache**: The `HistoricalProvider` caches yfinance lookups in the `market_data` library to speed up subsequent portfolio valuations.
- **Frontend State**: React state is used for session persistence, with `localStorage` serving as a bridge for user identity between refreshes.

---

## 4. Architectural Patterns

### 4.1 Fiduciary Engine (Agentic Architecture)
The platform uses a swarm of specialized agents to handle distinct parts of the fiduciary journey:

- **PathAllocator**: The core brain for asset allocation. Uses Modern Portfolio Theory (MPT) and risk-regime switching to build the optimal equity and passive sleeves.
- **InsightNarrativeEngine (INSA)**: The "Storyteller." Synthesizes quant data, risk metrics, and rebalance plans into human-readable, strategic narratives.
- **TaxOptimizationAgent (TOA)**: Scans tax lots for harvesting opportunities (STCG/LTCG) to minimize the tax drag of rebalancing.
- **PassiveFundResearchAssistant (PFRA)**: Harvests and filters the AMFI/passive universe to identify high-liquidity, low-tracking-error ETFs and Index Funds.
- **EquityResearchAssistant (EQRA)**: Provides deep-dive fundamental and quantitative metrics for specific symbols in the alpha sleeve.
- **GoalIntegrationAgent (GIA)**: Maps life goals (Survival, Safety, Growth) to specific target-date horizons and liability-matching strategies.
- **RiskAssessmentAgent (RAA)**: Analyzes user questionnaires and behavioral data to derive institutional-grade risk profiles.
- **RebalanceAgent (RBA)**: Calculates the precise trade instructions needed to migrate from the current to the proposed portfolio.
- **GovernanceAgent**: Monitors all agent outputs for compliance with ROCE constraints, sector caps, and UCITS 5/10/40 mandates.
- **SuperAgent**: The orchestrator that manages the flow of context and data between all specialized agents during a full review.

### 4.2 Staged Portfolio Updates
- **Pattern**: Command-Query Responsibility Segregation (CQRS) lite.
- **Workflow**: Users "Stage" changes (Add/Remove) in local frontend state. The "Optimization Manifest" is a preview (Query). Only when "Synchronized" (Command) is the data committed to the persistent DataStore.

### 4.3 AppShell Pattern
- A unified layout wrapper handles persistent navigation, branding, and global UI elements (like the INSA toggle), ensuring a seamless SPA (Single Page Application) experience.

---

## 5. Deployment & Environment
- **Environment Variables**: Managed via `.env` (Google/Groq API Keys, Master Encryption Key).
- **Database Path**: Defaults to `./data/arctic` (local LMDB).
- **API Client**: Centralized `api.ts` in the frontend for consistent error handling and type-safe requests.
