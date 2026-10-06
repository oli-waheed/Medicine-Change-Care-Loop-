# Initial Data Model

This document describes the initial data model for the Medicine Change Care Loop prototype.

## 1. Patient

A patient in this project is synthetic. No real patient data is used.

Fields:

- patientId
- name
- age
- email

Example:

patientId: P001
name: Anna Example
age: 65
email: anna@example.com

## 2. Medication Record

A medication record represents a medicine currently used by a synthetic patient.

Fields:

- medicationRecordId
- patientId
- medicineName
- productId
- vnr
- dosage
- status

Example:

medicationRecordId: M001
patientId: P001
medicineName: Example Medicine
productId: PROD001
vnr: 123456
dosage: 1 tablet daily
status: active

## 3. Medicine Change

This represents a detected change from medicine information.

Fields:

- changeId
- productId
- medicineName
- changeType
- oldValue
- newValue
- detectedAt
- evidenceStatus

Possible evidence status:

- verified
- inferred
- unknown
- conflicting

## 4. Review Case

A review case is created when a medicine change matches a synthetic medication record.

Fields:

- caseId
- patientId
- medicationRecordId
- changeId
- status
- createdAt
- assignedRole

Possible status:

- new
- under_review
- waiting_for_response
- closed

## 5. Relationships

Patient
↓
Medication Record
↓
Medicine Change Match
↓
Review Case