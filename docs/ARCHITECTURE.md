# ReqRipple Architecture Overview

This document outlines the design principles, structural boundaries, and technical architecture of ReqRipple.

## 1. Modular Monolith Architecture
ReqRipple is organized as a modular monolith:
1. **Domain Layer**: Pure business logic, independent of FastAPI or databases. Contains graph BFS traversal, explanation path generation, impact scoring heuristic, and workflow state machines.
2. **Services Layer**: Orchestrates database transactions, permission checks, entity life cycles, and delegates algorithmic computations to domain modules.
3. **API Layer**: Exposes versioned REST endpoints (`/api/v1`) using FastAPI with Pydantic request and response validation.
4. **Data Access Layer**: Relational models using SQLAlchemy 2.0 with foreign-key referential integrity and Alembic version-controlled schema migrations.

## 2. Graph Node Identity Design
Rather than relying on polymorphic foreign keys in the graph edge table, all graph entities (Requirements, Artifacts) map 1:1 to a record in `graph_nodes`. `traceability_edges` connect `graph_nodes(id)` as `source_node_id` and `target_node_id`, guaranteeing true database foreign keys and clean join performance.
