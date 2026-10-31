/*
  Becoming Doom launch configuration.
  Every public date, price and connection lives here. Change it once and every page updates.
  Nothing on the site hard-codes these values.
*/
window.DOOM_CONFIG = {
  // Set to true only when Edem has confirmed price, dates and places.
  // While false, every page shows a small "draft" notice and the buy button stays disabled.
  launchConfirmed: false,

  cohort: {
    name: "Founding cohort",
    priceGBP: 297,            // proposed, not confirmed
    places: 8,                // proposed, not confirmed
    // All times are Europe/London. Three distinct events, never merged into one clock.
    enrolmentCloses: "2026-11-05T23:59:00+00:00",
    courseStarts: "2026-11-06T09:00:00+00:00",
    doomsday: "2026-12-18T19:00:00+00:00",   // final demonstration, day after day 42
    councilDay: "Saturday",
    hoursPerWeek: "about 6",
  },

  // Email capture for The First No.
  // provider: "kit" | "mailerlite" | "custom" | "" (empty = not connected yet)
  // kit:        action = "https://app.kit.com/forms/<FORM_ID>/subscriptions"
  // mailerlite: action = the form action URL from MailerLite's HTML embed code
  // custom:     any endpoint that accepts a POST with first_name and email
  email: {
    provider: "",
    action: "",
  },

  // Application form. Leave applyUrl empty to use the built-in form on apply.html,
  // which posts JSON to applyEndpoint (for example a Formspree form endpoint).
  // Or set applyUrl to a hosted Tally/Typeform link and the Apply buttons go there instead.
  applications: {
    applyUrl: "",
    applyEndpoint: "",
  },

  // Checkout link from Whop once the product exists. Only shown to accepted applicants.
  checkoutUrl: "",

  contact: {
    xHandle: "",               // e.g. "becomingdoom" (without @)
    email: "",                 // a reply-to address for questions and privacy requests
    telegram: "",              // full t.me link
  },
};
