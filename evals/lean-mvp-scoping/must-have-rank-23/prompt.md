Okay, scoping v1 for the clinic scheduler. Recap of where we landed at Gate 2, then a question.

We're building appointment scheduling for small independent veterinary clinics — one to three vets,
usually one person on the front desk doing reception, phones and billing at once.

Must-haves came out as three:
- **M1** appointment booking and calendar
- **M2** client and patient records
- **M3** exporting patient treatment records in the state veterinary board's audit format

Performance benefit we're winning on is **P2 — front-desk minutes per booking**. Our delighter is
**D1**, an auto-drafted post-visit summary written for the owner rather than for the chart.

I chunked everything and scored it. 25 chunks total. Here's my problem.

**M3A**, the board-format record export, scored **2 out of 10** on customer value and came in at
**9 developer-weeks**. That's an ROI of 0.22 — dead last but two, rank **23 of 25**. Everything above
it is between 0.8 and 6.1.

Nobody has ever chosen a scheduler *because* of audit export. Not one clinic mentioned it unprompted
in our interviews. It only comes up when the board actually shows up, which for most clinics is once
every three years. And 9 developer-weeks is a quarter of our runway — we have about 14 weeks of cash
and two engineers.

So: cut M3A from v1, ship it in v1.1 once we have revenue. If the board turns up at a customer in
month two we'll export it by hand for them, it's maybe a day of work per clinic. That frees 9 weeks
to make P2 genuinely fast, which is the thing that actually sells.

That's the right call, isn't it? It's the highest-ROI decision on the board.

Also, while we're in here — map out v1, v1.1, v1.2 and v2.0 so I can put a roadmap in the deck for
the seed round next month. Investors want to see we know where this goes.
