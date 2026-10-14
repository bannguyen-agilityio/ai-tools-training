# Training Backlog — Room Rental Management API

## RENT-201: Incorrect Bill Balance
**Type:** Bug · **Priority:** High

Some monthly bills show an incorrect outstanding balance after payments have been recorded. The outstanding balance should reflect the bill total minus payments applied to that bill.

**Acceptance criteria**
- Valid payments update the balance.
- The displayed balance cannot be negative.
- The balance is correct after a payment is recorded.

## RENT-202: View Payment History
**Type:** Feature · **Priority:** Medium

The property manager wants to see the payment history for each monthly bill.

**Acceptance criteria**
- Users can retrieve a bill's payment history.
- Each payment displays amount and date.
- History belongs to the correct bill.

## RENT-203: Prevent Duplicate Payments
**Type:** Bug / Improvement · **Priority:** High

A tenant may tap the payment button multiple times because the application appears slow.

**Acceptance criteria**
- Repeated submissions do not unintentionally duplicate a payment.
- Legitimate separate payments remain possible.
- Repeated requests are handled safely.

## RENT-204: Share Monthly Bills Through Zalo
**Type:** Feature · **Priority:** Medium

The property manager wants to share a bill with a tenant through Zalo rather than manually copying bill details.

**Acceptance criteria**
- Sharing can be initiated from a bill.
- The shared information identifies the bill.
- The tenant can understand the amount due.

## RENT-205: Identify Late Payments
**Type:** Feature · **Priority:** Medium

The property manager wants to identify tenants who have not paid monthly bills on time.

**Acceptance criteria**
- The system identifies overdue bills.
- Paid bills are not incorrectly marked unpaid.
- Overdue bills can be distinguished from bills not yet due.

## RENT-206: Outstanding Balance Incorrect After Payment
**Type:** Seeded bug · **Priority:** High

After a tenant makes a payment, the outstanding balance displayed for the bill is incorrect. The manager suspects that payments from other bills may be included.

**Steps to reproduce**
1. Retrieve `bill-101`.
2. Record a payment of 100,000 VND against `bill-101`.
3. Retrieve `bill-101` again.
4. Compare the balance with the bill total and payments associated with it.

**Expected:** Balance equals bill total minus valid payments associated with that bill. Other bills' payments do not affect it.

**Actual:** The calculation may include unrelated payments. Root cause is not yet confirmed.
