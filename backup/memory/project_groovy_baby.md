---
name: project-groovy-baby
description: "Groovy Baby — Flutter baby tracker app with Firebase, multi-caregiver sharing, offline-first"
metadata: 
  node_type: memory
  type: project
  originSessionId: 34c8f2f7-c707-4887-a549-ec42c857a165
---

Groovy Baby is a Flutter baby tracking app for logging feeds, sleep, diapers, growth, and milestones.

**Stack:** Flutter + Firebase (Auth, Firestore, Cloud Functions), Riverpod, GoRouter, fl_chart
**Platforms:** iOS, Android, Web
**Auth:** Email/password, Google, Apple Sign-In
**Key features:** Multi-child, multi-caregiver (family-based sharing with roles), offline-first with eventual consistency

**Why:** Clean personal-use baby tracker, with future ambitions for insights, data import/export, and healthcare interop (Epic/FHIR, pediatrician data sharing).

**How to apply:** Data model uses FHIR-friendly field naming from the start. Flat event collection (not subcollections) for easier export and cross-child queries. Plan at ~/plans/groovy-baby/plan.md. Related to [[project-gofish]] as another Flutter/Firebase app — similar patterns apply.
