# 🧠 Prompt Manager – Technical Implementation Blueprint

## 1. System Overview

The **Prompt Manager** will operate in two distinct modes designed to accommodate flexible prompt storage and lifecycle management:

* **Globo Mode (Database-based)** – For enterprises and large-scale systems requiring relational DB-backed prompt storage and versioning.
* **Filo Mode (File-based)** – For local or lightweight setups, storing prompts as structured YAML/JSON files within a directory system.

Both modes can coexist or be combined, ensuring consistent handling of prompts, versioning, and schema integrity across environments.

---

## 2. Core Architectural Principles

### 2.1 Immutability

Prompts are immutable once created. Any modification generates a new version record in DB (Globo) or a new timestamped file in file storage (Filo).

### 2.2 Declarative Configuration

All configurations are driven by environment variables and YAML files.

* `PROMPT_PATH`: Defines root directory for prompt storage.
* `PROMPT_MODE`: Defines operational mode (`globo`, `filo`, or both).

### 2.3 Database Agnostic

The application supports all major relational databases (PostgreSQL, MySQL, SQLite, MSSQL) via **SQLAlchemy ORM**, while intentionally excluding NoSQL backends.

### 2.4 Common Schema Design

All databases share a uniform schema structure under the namespace `prompts_store`.

---

## 3. Database Schema (Globo Mode)

### Schema: `prompts_store`

Contains two primary tables:

#### 3.1 Table: `in_house_prompt`

Stores active prompts.

| Column        | Type         | Description                                          |
| ------------- | ------------ | ---------------------------------------------------- |
| id            | INT (PK)     | Unique identifier                                    |
| use_of        | VARCHAR (PK) | Business key identifying usage, e.g., `patient_info` |
| system_prompt | TEXT         | System-level context prompt                          |
| user_prompt   | TEXT         | User-facing input prompt                             |
| description   | TEXT         | Description or contextual notes                      |
| token_length  | INT          | Combined system + user prompt token count            |
| task          | VARCHAR      | Short label describing task category                 |
| agent_name    | VARCHAR      | Optional identifier for LLM agent or module          |
| meta_info     | JSON         | Stores model and environment details                 |
| meant_for     | ENUM         | One of (`vision`, `language`, `code`, `validation`)  |

#### 3.2 Table: `previous_prompt`

Maintains historical versions of prompts.

| Column     | Type                     | Description                             |
| ---------- | ------------------------ | --------------------------------------- |
| version_id | INT (PK)                 | Version identifier                      |
| id         | FK to in_house_prompt.id | Parent prompt reference                 |
| modified   | TIMESTAMP                | Timestamp when new version was created  |
| diff       | JSON                     | Computed difference between versions    |
| snapshot   | JSON                     | Serialized previous state of the prompt |

---

## 4. File-Based Mode (Filo Mode)

### 4.1 Folder Structure

```
prompts_store/
│
├── current/              # active prompts
│   ├── patient_info_2025-11-10-14-00.yml
│   ├── summarizer_2025-11-10-14-03.yml
│
├── versions/             # archived versions
│   ├── patient_info_2025-11-10-13-50.yml
│   ├── summarizer_2025-11-09-17-00.yml
```

### 4.2 Versioning

Each prompt file name is timestamped using the pattern:
`<usage>_<YYYY-MM-DD-HH-MM>.yml`

Whenever content changes (even one character), the system compares the checksum of new vs existing content, generates a diff, and moves the old file to `versions/`.

### 4.3 Validation

Filo uses YAML schema validation before saving files. It also enforces immutability — direct edits on disk outside controlled APIs will raise errors.

---

## 5. Application Configuration

### Configuration File Template (`config.yml`)

```yaml
PROMPT_PATH: "/app/prompts_store"
PROMPT_MODE: "globo"  # or "filo" or both

DATABASE:
  ENABLED: true
  ENGINE: postgresql
  HOST: localhost
  PORT: 5432
  USER: admin
  PASSWORD: secret
  NAME: promptdb

GLOBO_MODE: true
FILO_MODE: false
```

### Initialization Workflow

1. On first run, the application generates this configuration file.
2. YAML templates are auto-populated with database and path defaults.
3. Upon startup, `PromptManager` checks mode flags to determine DB/file routing.

---

## 6. Application Bootstrapping Flow

1. **Initialization Phase**

   * Load `.env` or `config.yml`
   * Validate mode settings
   * Initialize SQLAlchemy engine (for Globo)
   * Initialize directory structure (for Filo)

2. **YAML Template Creation Phase**

   * During installation, pre-create YAML config for prompt metadata.
   * Templates define prompt schema and validation fields.

3. **Runtime Phase**

   * Prompts can only be registered, updated, or versioned via YAML.
   * CLI or API calls invoke creation or modification, not manual file edits.

4. **Inference Phase**

   * Calls like `pm.infer(usage="patient_info")` automatically resolve to the relevant file or DB row.
   * Lookup based on `use_of` (the business key).

5. **Versioning Phase**

   * Content diff engine detects change.
   * New prompt version is written to DB (Globo) or moved to archive folder (Filo).

---

## 7. Enforcement & Validation

* **Access Control:** No direct write access to DB or file system outside controlled API/CLI.
* **Schema Enforcement:** All prompt fields (`system_prompt`, `user_prompt`, etc.) validated against YAML-defined schema.
* **Error Handling:** Custom exception classes for `SchemaViolationError`, `ImmutableWriteError`, `ModeMismatchError`.
* **Audit Logging:** Each CRUD operation logged with timestamp, username, and mode.

---

## 8. Implementation Questions (and Proposed Solutions)

### 1. **How to Form Immutable Store Class?**

* Create a base `ImmutableStore` abstract class.
* Override `insert()` and `update()` to enforce immutability (insert only, no updates).
* For Filo mode, this translates to copy-on-write file handling.

### 2. **How to Dynamically Create Tables Across Clients?**

* Use SQLAlchemy `MetaData` reflection with dynamic schema creation.
* Each client can have an isolated schema or shared schema partitioned by tenant ID.

### 3. **How to Handle Mode and Path Dynamically?**

* Factory pattern: `StorageFactory(mode)` returns `FiloStorage` or `GloboStorage`.
* Path and mode loaded from environment variables on startup.

### 4. **Naming Conventions**

* Database: `in_house_prompt`, `previous_prompt`
* Files: `<usage>_<timestamp>.yml`
* Config keys: Upper snake case (e.g., `PROMPT_MODE`, `PROMPT_PATH`)

### 5. **Data Flow**

```
User → CLI/API → YAML Template → Validation Layer → Storage Handler (Globo/Filo) → Version Manager → Audit Logger
```

### 6. **Auditing**

* DB Mode: Insert into `audit_log` table.
* File Mode: Append audit details to `audit.yml`.
* Each entry: timestamp, author, action, checksum, diff ref.

### 7. **Prompt CI/CD Lifecycle**

* Implement GitHub Actions or GitLab CI pipeline:

  * Validate prompt syntax.
  * Auto-generate documentation from YAML.
  * Test schema and lint YAML files.
  * Push validated prompts to central registry or DB.

### 8. **Model Inference Wrapper**

* Include `InferenceManager` module.
* Supports OpenAI and Groq APIs initially.
* Abstracts API key handling, retries, and response normalization.

---

## 9. Tech Stack Overview

| Layer              | Technology                   |
| ------------------ | ---------------------------- |
| Backend Framework  | FastAPI / Flask              |
| ORM                | SQLAlchemy                   |
| File Validation    | PyYAML, Pydantic             |
| CLI                | Typer or Click               |
| Version Diff       | DeepDiff / custom hashing    |
| Logging & Auditing | Loguru, structured JSON logs |
| Testing            | Pytest, SQLite memory DB     |
| Deployment         | Docker + GitHub Actions      |
| Docs               | MkDocs or Sphinx             |

---

## 10. Summary

This architecture unifies **database-backed (Globo)** and **file-based (Filo)** prompt management under a single cohesive framework. It supports immutability, version tracking, schema validation, auditing, CI/CD integration, and modular inference interfaces for OpenAI/Groq.

The implementation blueprint provides a scalable foundation for prompt lifecycle automation, aligning with software engineering best practices while remaining flexible enough for local experimentation or enterprise-scale deployment.
