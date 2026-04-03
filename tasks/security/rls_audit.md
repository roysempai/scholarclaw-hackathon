# Security Audit: Row-Level Security
## Status: PENDING — runs after Phase 0-B

### Purpose
Review RLS policies to ensure users can only access their own data.

### Checklist
- [ ] RLS enabled on all user-scoped tables
- [ ] SELECT policies restrict to owner
- [ ] INSERT policies validate ownership
- [ ] UPDATE policies validate ownership
- [ ] DELETE policies validate ownership (or disabled)
- [ ] Admin bypass properly scoped
- [ ] Service role access documented

### Tables to Audit
- users
- profiles
- applications
- audit_logs
- attack_logs
- refresh_tokens

### Findings
*To be filled after Phase 0-B completion*

### Recommendations
*To be filled after Phase 0-B completion*
