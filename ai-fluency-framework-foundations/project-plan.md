# Project plan: Household rental room management app

## Project vision and goals

### Vision

Build a simple mobile app that helps a household manage rental rooms, replacing its current Excel workflow.

### Goals

- Manage rooms, monthly bills, rates, and payment status in one place.
- Reduce manual work and billing mistakes.
- Share bill images and bank payment QR codes with tenants through Zalo.
- Keep records accessible on a phone.
- Support backup and restoration through JSON files.

### What success looks like

- The household can complete monthly billing without Excel.
- Bill amounts are accurate and easy for tenants to understand.
- Sharing bills and payment details through Zalo takes only a few steps.
- The household can quickly identify paid and unpaid bills.
- Records remain available after closing and reopening the app.
- A backup can successfully restore the household’s records.

### Why this project is valuable

The app saves time on monthly billing, reduces repetitive work, and makes collecting rent easier for the household.

## Overall delegation

### Handle myself

- Define household needs, billing rules, and priorities.
- Provide anonymized sample data
- Make final decisions about features and design.
- Verify bill amounts and bank payment details.
- Test with the household and approve the release.

### AI contribution

- Suggest technical options and explain trade-offs.
- Draft code and propose UI designs.
- Develop relevant tests and help investigate bugs.
- Prepare build configuration and release instructions.

### Work together

- Break the project into manageable tasks.
- Discuss assumptions and implementation choices.
- Review code, calculations, and user workflows.
- Improve the app based on household feedback.

## Task breakdown and delegation

### 1. Project setup

- Skills needed: Expo, React Native, and project configuration.
- Handle myself: Choose target devices and confirm household needs.
- AI contribution: Set up the project with a Vietnamese UI and explain configuration choices.
- Collaboration: Review the structure and resolve setup issues.

### 2. Local storage

- Skills needed: Data modeling, local persistence, and validation.
- Handle myself: Explain the existing Excel structure and provide anonymized examples.
- AI contribution: Design and implement storage for rooms, bills, and rates.
- Collaboration: Check that records persist and that rate changes do not alter historical bills.

### 3. Core features

- Skills needed: UI development, billing calculations, and payment tracking.
- Handle myself: Define rent, electricity, water, and other fee rules; provide Vietnamese wording; verify expected amounts.
- AI contribution: Implement room management, monthly bills, paid/unpaid tracking, and rate settings.
- Collaboration: Test realistic billing cases and simplify the monthly workflow.

### 4. Default bank payment QR

- Skills needed: Payment QR generation and settings management.
- Handle myself: Provide bank details and verify the payment recipient.
- AI contribution: Implement bank settings that can be entered once and reused on every bill.
- Collaboration: Decide whether the QR includes the bill amount and payment reference, then verify it by scanning.

### 5. Sharing through Zalo

- Skills needed: Bill image generation and mobile sharing integration.
- Handle myself: Approve the bill layout and test sharing on a real phone.
- AI contribution: Investigate supported sharing options and implement bill image generation and the sharing flow.
- Collaboration: Confirm the actual Zalo behavior and check that tenants receive readable bills and usable payment details.

### 6. Backup and restore

- Skills needed: JSON export/import, file handling, and data validation.
- Handle myself: Decide where to keep backups and whether imports replace or merge existing records.
- AI contribution: Implement export, import, validation, and error handling.
- Collaboration: Test restoration and confirm that records and bill amounts remain correct.

### 7. Testing and release

- Skills needed: Visual design, dark mode, testing, and EAS Build configuration.
- Handle myself: Select the icon, test with the household, manage required accounts, and approve the release.
- AI contribution: Propose icon concepts, implement dark mode, write relevant tests, help fix issues, and configure builds.
- Collaboration: Review usability, test results, and the final installation before release.
