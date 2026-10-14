# Training Backlog — Room Rental Management API

## RENT-201: Incorrect Bill Balance

**Type:** Bug
**Priority:** High
**Reporter:** Property Manager

### Description

Some monthly bills show an incorrect outstanding balance after payments have been recorded. The property manager reported that the amount displayed on the bill does not always match the amount expected.

### Expected Result

The outstanding balance should reflect the bill total minus the payments applied to that bill.

### Acceptance Criteria

- The outstanding balance reflects valid payments.
- The displayed balance cannot be negative.
- The balance is correct after a payment is recorded.

---

## RENT-202: View Payment History

**Type:** Feature Request
**Priority:** Medium
**Reporter:** Property Manager

### Description

The property manager wants to see the payment history for each monthly bill so they can understand how and when tenants have paid.

### Expected Result

Users should be able to view the payment history associated with a bill.

### Acceptance Criteria

- Users can retrieve the payment history for a bill.
- Each payment displays its amount and date.
- The history is associated with the correct bill.

---

## RENT-203: Prevent Duplicate Payments

**Type:** Bug / Improvement
**Priority:** High
**Reporter:** Property Manager

### Description

A tenant sometimes taps the payment button more than once because the application appears slow. The manager is concerned that the same payment could be recorded multiple times.

### Expected Result

The system should avoid recording duplicate payments when a request is accidentally submitted more than once.

### Acceptance Criteria

- Repeated submissions do not unintentionally duplicate a payment.
- Legitimate separate payments can still be recorded.
- The system handles repeated requests safely.

---

## RENT-204: Share Monthly Bills Through Zalo

**Type:** Feature Request
**Priority:** Medium
**Reporter:** Property Manager

### Description

The property manager wants to send monthly bills to tenants through Zalo instead of manually copying bill details into messages.

### Expected Result

Users should be able to share a bill with a tenant through Zalo.

### Acceptance Criteria

- Users can initiate sharing from a bill.
- The shared information identifies the relevant bill.
- The tenant receives enough information to understand the amount due.

---

## RENT-205: Identify Late Payments

**Type:** Feature Request
**Priority:** Medium
**Reporter:** Property Manager

### Description

The property manager wants to identify tenants who have not paid their monthly bills on time.

### Expected Result

The application should identify overdue bills so the manager can follow up with tenants.

### Acceptance Criteria

- The system can identify bills that are overdue.
- Paid bills are not incorrectly marked as unpaid.
- Users can distinguish overdue bills from bills that are not yet due.

---

## RENT-206: Outstanding Balance Incorrect After Payment

**Type:** Bug — Seeded for Training
**Priority:** High
**Reporter:** Property Manager

### Description

After a tenant makes a payment, the outstanding balance displayed for the bill is incorrect.

The manager suspects that the system may be including payments from other bills when calculating the balance.

### Steps to Reproduce

1. Retrieve bill `bill-101`.
2. Record a payment of 100,000 VND against `bill-101`.
3. Retrieve `bill-101` again.
4. Compare the outstanding balance with the bill total and payments associated with that bill.

### Expected Result

The outstanding balance should equal the bill total minus the valid payments associated with that bill.

Payments associated with other bills must not affect the balance.

### Actual Result

The displayed outstanding balance may be incorrect because the balance calculation may include unrelated payments.

### Acceptance Criteria

- Only payments belonging to the requested bill affect its outstanding balance.
- Recording a valid payment updates the balance correctly.
- The balance remains correct when other bills have payments.
- Automated tests cover the calculation.

### Developer Notes

The root cause has not been confirmed. Reproduce the problem, inspect the relevant code, and verify any proposed explanation before implementing a fix.
