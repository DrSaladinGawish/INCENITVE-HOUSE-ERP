# BIO ERP Doctor-Patient Protocol v1.0 (Corrected)
## Canonical Relationship Framework — EventCore (Patient) Edition

---

### Role
**EventCore is the PATIENT.** Bio-ERP (`D:\ERP System\BIO_ERP\`:8000) is the DOCTOR.

### What EventCore MUST do:
- Collect raw operational data (symptoms)
- Clean/validate data before pushing to Doctor
- Push clean records via `POST /api/v1/bio-sync/push-all` to Doctor
- Accept prescriptions from Doctor at `POST /api/v1/eventcore-bridge/or-insights`
- Display Doctor's prescriptions on dashboard
- Flag corrupted data as `data_gap_permanent` — never hide it

### What EventCore MUST NOT do:
- Run advanced analytics locally (LP, EOQ, PERT, SCM costing)
- Push unvalidated imports without density checks
- Modify production data based on local guesses
- Self-diagnose

### Current Status:
- 1.3% density (45/3,598 rows clean)
- 9 invoices ($2.23M) = clean → analyze
- 2,938 bank transactions = corrupted source → exclude
- 365 purchase invoices = missing child records

### Key Endpoints:
| Direction | Endpoint | Port |
|-----------|----------|------|
| Patient → Doctor | `POST /api/v1/bio-sync/push-all` | :8001 → :8000 |
| Exclusions check | `GET /api/v1/bio-sync/exclusions` | :8001 |
| Doctor → Patient | `POST /api/v1/eventcore-bridge/or-insights` | :8000 → :8001 |

### Directory Map:
- Doctor: `D:\ERP System\BIO_ERP\` (:8000)
- Patient: `D:\EventCore_ERP\` (:8001)
- SCM Module Patient: `D:\SCM Module\`
- OR-ERP: inside Bio-ERP at `/api/v1/or/`

### Protocol Version: 1.0 (Corrected)
### Canonical Source: Memory ID 19
