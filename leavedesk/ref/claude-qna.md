# Prompt
I'm the HR manager at a 250-person company. Here's my problem: "We need a simple internal tool for leave requests. Staff should be able to request leave, managers approve it, and HR can see everything. It should calculate how many days people have left. Public holidays shouldn't count. Something like a team calendar would be great too. We'd like to start using it next month. Budget is limited, so keep it simple."
Interview me like a business analyst — scope, users, constraints, what success looks like —
one question at a time, until the idea is concrete.

1. How are leave requests handled right now? For example, email, a shared spreadsheet, paper forms, or something else. What's the biggest pain point with that?

    I currently track leave requests in Excel files. The biggest pain point is that checking and updating the records and preparing monthly reports takes too much time and is a very slow, manual process.

2. Roughly how many leave requests do you get in a typical month, and how much of your time does the Excel upkeep and monthly reporting take? A rough guess is fine, for example "about 40 requests and two days a month."

    About 150 requests and 2 days a month.

3. What types of leave do you need to track, and how is each one's balance worked out? For example, annual leave with a fixed yearly allowance, sick leave, unpaid leave, or others. Please also say whether unused days carry over to the next year and whether the allowance depends on years of service.

    Annual leave: 12 days per year. Sick leave: 7 paid days per year. Unpaid leave: no limit. Unused leave days can be carried over to the following year.

4. Is there a cap or expiry on the carried-over days? For example, all unused days carry over forever, only up to X days carry over, or carried-over days must be used by a certain month. Does the same apply to sick leave, or only to annual leave?

    Only annual leave carries over, up to 6 days. Sick leave does not carry over. (Decided 2026-10-28: carried days are not carried again; the cap applies to the current year's unused days.)

5. Do carried-over days expire, or can they be used any time during the new year? Also, does your leave year run January to December, or does it follow a different cycle?

    Carried-over days expire at the end of the following year. The leave year runs from January to December.

6. Who approves a request? Is it each person's direct manager, and what happens if that manager is away? Does HR need to sign off too, or does HR only see approved leave?

    The employee's direct manager approves leave requests. Managers' own requests go to HR. HR only views approved leave. If a manager is unavailable, the employee can ask another manager to approve the request.

7. Can people request half days or partial days, or only full days? Also, are there rules like minimum notice for annual leave, or a manager being allowed to reject a request? If so, does a rejection need a reason?

    Employees can request half-day leave (morning or afternoon). Managers can reject requests but must provide a reason. Minimum notice is 1 day for a single day off and 1–2 weeks for leave longer than one week. (Decided 2026-10-28: 1 week, warning only, for more than 5 working days.)

8. Which days count as working days, and how do you handle public holidays? Is it Monday to Friday only, or do some staff work Saturdays? Who maintains the holiday list: should HR enter the dates each year, or do you want it pre-loaded for your country? Which country is that?

    Working days are Monday–Friday, excluding Vietnamese public holidays (revised 2026-10-28; originally US). HR maintains the holiday list annually, preloaded with Vietnamese holidays.

9. Who can see what on the team calendar? Should everyone see who is off, including the leave type, or just "Name – away"? Does it show only approved leave, or pending requests as well? Is it company-wide, or does each person only see their own team?

    Employees see their own team's approved and pending leave. HR sees all teams. Sick leave is displayed as “Off” to colleagues to protect privacy.

10. How should people sign in, and how should they be notified? Does the company use Google Workspace or Microsoft 365 that everyone could sign in with, or would you need separate usernames and passwords? Is email notification enough ("new request waiting", "approved/rejected"), or would you want Slack or Teams messages too?

    Use Google Workspace emails (@asnet.com.vn) and passwords for login. Email notifications. Add Google SSO later.

11. What does your monthly report contain today? For example, leave taken per person by type, remaining balances, who was off and when, or totals per team. Which of these would you want exported to Excel or PDF?

    HR needs a monthly Excel-compatible report showing leave taken per employee by type, remaining balances, and who was off and when.

12. What does success look like a few months after launch? For example, the monthly report takes minutes instead of 2 days, nobody asks HR "how many days do I have left?", or requests no longer get lost. Which of these matters most, and is there a number you'd use to call it a win?

    No leave requests by email after launch; HR month-end takes under 10 minutes; no balance corrections

13. How will the current balances get into the system? For example, HR enters each person's remaining annual and sick days as of the launch date, or we import them from your Excel files. Are those files clean and consistent enough to import? Do you also need past leave history in the tool, or only balances from the start date?

    HR enters each person's remaining balances by hand.

14. What happens when plans change after a request is submitted or approved? Can employees cancel their own request at any time, or only before it's approved, and do they need approval to cancel once it's approved? Can HR edit or cancel leave on someone's behalf?

    Employee can cancel while Pending. Once Approved, only HR can cancel; days are refunded

15. Who sets up and maintains the people and teams in the tool? Does HR add each person with their team and manager, and handle new joiners and leavers? For someone who joins mid-year, do they get the full 12 and 7 days or a pro-rated amount?

    HR manages employees, teams, and managers. New joiners receive pro-rated annual and sick leave. HR is 2 people: the HR owner and a deputy (2026-10-28).

16. What are the budget and hosting constraints? Roughly what can you spend, as a one-off and per month? Is there anyone in the company who can look after it technically (hosting, backups, fixing problems) after launch, or will it need to be as hands-off as possible? Is there a hard date next month when it must be live?

    Under $5/month, with a developer available for support.

17. Is there a hard go-live date next month, and if time runs short, what could wait? Of everything we've covered, what's essential on day one (requests, approval, balances, email notices) and what could come in a second phase (team calendar, Excel report, SSO)?

    Go live on November 1; everything is essential except SSO

18. Is it workable for one person by 1 November? If not, we could load people in batches, for example managers and early users first. Which would you prefer?

    Yes, it is.
