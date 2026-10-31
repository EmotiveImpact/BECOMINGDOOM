# Launch funnel

Status 31 October 2026: built and ready for review. Draft mode is on, so the site shows a notice and checkout is disabled until the founder confirms price, dates and places.

## The funnel in one line

X post → comment "NO" → personal reply with the link → [free lesson page](../site/index.html) (name and email) → [lesson and workbook](../site/lesson.html) → [7-day email sequence](EMAIL_SEQUENCE.md) → [cohort page](../site/cohort.html) → [application](../site/apply.html) → short conversation → checkout link for accepted applicants.

## What is in this folder

| File | Purpose |
|---|---|
| [EMAIL_SEQUENCE.md](EMAIL_SEQUENCE.md) | Seven emails from sign-up to applications opening, ready to paste into Kit or MailerLite |
| [POSTS_14_DAYS.md](POSTS_14_DAYS.md) | Fourteen days of X posts, morning and evening, written in full |
| [SALES_CONVERSATIONS.md](SALES_CONVERSATIONS.md) | Application review, DM and call script, follow-ups and objections |
| [CHECKOUT_PRODUCT.md](CHECKOUT_PRODUCT.md) | Product listing copy and settings for the checkout platform |

The website lives in [site/](../site/). It is plain HTML, CSS and JavaScript with no build step.

## Decisions still open

Every public value lives in `site/assets/config.js`. Change it there and every page updates.

| Decision | Current proposal | Where to change |
|---|---|---|
| Founding price | £297 | `cohort.priceGBP` |
| Places | 8 | `cohort.places` |
| Applications close | Thursday 5 November, 23:59 UK time | `cohort.enrolmentCloses` |
| Course starts | Friday 6 November | `cohort.courseStarts` |
| Doomsday demonstration | Friday 18 December, 19:00 UK time | `cohort.doomsday` |
| Refund policy | Full refund if requested after doing the week one work and before week two starts | FAQ in `site/cohort.html` |
| Email tool | Kit or MailerLite | `email.provider` and `email.action` |
| Application storage | Built-in form posting to Formspree, or a hosted Tally form | `applications` |
| Checkout | Whop product link | `checkoutUrl` |
| Founder bio and photo | Not written; the sales page names Edem only as course designer | `site/cohort.html` |

A six-day window from today to 6 November is tight for an audience built from scratch. The playbook's suggestion still stands: fill the founding cohort mainly from people Edem already knows and early followers, and use X to build the list for a January cohort. If the start moves, change the three dates in config and the copy in the email and post files that mentions them.

The website spec ties the finale to 18 December (the US date for the Doomsday film). Disney+ UK lists 16 December. The site labels 18 December as our own demonstration date and never claims a link to the film's release.

## Going live, in order

1. Confirm the decisions above and edit `site/assets/config.js`.
2. Create the email form in Kit or MailerLite. Copy its form action URL into `email.action` and set `email.provider`. Add the seven emails as an automation triggered by that form.
3. Create a Formspree form (or a Tally form) for applications and set `applications.applyEndpoint` (or `applications.applyUrl` for Tally).
4. Create the product on Whop using [CHECKOUT_PRODUCT.md](CHECKOUT_PRODUCT.md). Set `checkoutUrl` to its link. Send that link only to accepted applicants.
5. Add `contact.email` and `contact.xHandle`.
6. Deploy: import the repository into Vercel with the root directory set to `site`. No build command or framework is needed.
7. Test end to end with a real email address: sign up, receive email one, submit an application, open checkout.
8. Set `launchConfirmed: true`. The draft notice disappears and the checkout button goes live.

To preview locally: `cd site && python3 -m http.server 8000`, then open http://localhost:8000.

## Measure every Sunday

Followers, post impressions, comments on lead posts, sign-ups, email open and reply rates, applications, conversations, places sold. The number that matters most is sign-ups to conversations. If people take the lesson and never reply, rewrite email two first.

## Rules this funnel keeps

From the [charter](../PROJECT_CHARTER.md) and the playbook:

- No outcome, income or transformation claims before the pilot has run. No invented testimonials.
- Real scarcity only: the true number of places and a real start date. No fake countdowns that reset.
- One real X account. No automated accounts, engagement groups or bought engagement.
- Payment processors used within their terms.
- Marketing email only with explicit consent, with an unsubscribe link in every email.
- Workbook answers stay in the visitor's browser and are never collected.
