# Project Architectural Ledger & Feature History (Permanent)

## 1. System Topology & Core Invariants
- **Hub (`D3Nexus`)**: Physical SSOT for `shared-contracts/`, Rust core + FastAPI engine, Flutter client.
- **Satellites (`lyrics-sync`, `nexus`)**: Outbound symlinks to `shared-contracts/`, mechanically verified by `check_contracts.py`.
- **Workflows (`ai-agent-tools`)**: Bilingual TOC (`doc-designer`), Contract-First `task_01` sequencing (`dev-designer`).

## 2. Completed Epics & Architectural Milestones
- **[2026-10-31] `context_memory_management`**: Delivered Two-Tier Project Memory, Tri-Role Governance, Shell Environment Sync, and Dev-Lifecycle Context Hooks
- **[2026-10-31] `context_memory_quick_guide`**: Published bilingual Context Memory & Tri-Role Workflow Quick-Guide (docs/context-memory-quick-guide.en.md & .vi.md) and updated lifecycle diagrams with Tri-Role personas
