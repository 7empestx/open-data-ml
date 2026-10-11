---
title: Work with us
description: A free two-week pilot for wind operators. Send a year or more of SCADA exports and status logs, and get a written condition report on your fleet.
---

open-data-ml is run by Beehive AI Labs LLC. We offer wind O&M teams three things, all built on the same methods published on this site:

- **Health assessment.** A one-off written review of a wind farm's SCADA data and status logs, like the [sample condition report](/windml/condition-report/).
- **Condition monitoring.** The same checks repeated on new data at an interval that suits you, with changes since the last report called out.
- **Free pilot.** A first health assessment on one site at no cost, so you can judge whether it's useful before anything else.

## The free pilot

**What it is.** We run your data through the same cleaning, labeling and condition checks used for Kelmarsh and Penmanshiel, then write up what we find. It's a retrospective review, not a failure prediction. Our own tests show that 10-minute SCADA data can't reliably predict faults ahead of time, and we won't claim otherwise. See [Results](/windml/results/).

**What you get, about two weeks after we receive your data:**

- A written report (PDF) with a per-turbine scorecard and a red, amber or green flag for each turbine.
- Availability and lost production by cause, per turbine and per year.
- Chronic abnormal states, such as oil pressures or temperatures sitting away from normal for weeks or months.
- Sensor health: frozen, drifting or mis-scaled channels, and gaps in the data.
- A short list of specific things for your engineers to check, each with the evidence behind it.
- A call to walk through the findings and answer questions.

**What it costs.** Nothing. There's no obligation to buy anything afterwards.

## What data we need

**Required:**

- **10-minute SCADA data** for at least 12 months, ideally 2 years or more. Averages are enough. Minimum, maximum and standard deviation columns help if your system exports them.
- **Turbine status or alarm logs** for the same period, with the status code, message, and start and end times.
- **Basic site details:** turbine make, model and rating, and turbine IDs.

**Helpful if you have them:**

- Maintenance or work-order records, such as component replacements, oil changes and inspections.
- Oil analysis or vibration reports.
- Any known changes during the period, such as control software updates or sensor replacements.

**Format.** Whatever your system exports is fine: CSV, Excel or Parquet, from Greenbyte, Bazefield, your OEM portal or your own historian. We map it to our format, so you don't need to reshape anything.

## How your data is handled

- Your data stays yours. We use it only for your report.
- It's never published, shared or added to public results without your written permission.
- Before you send anything, we agree in writing where it will be stored, who can see it, and when it will be deleted. We're happy to work under your NDA or data-sharing agreement.
- Check your turbine service contract first. Some contracts limit sharing SCADA data with third parties.

## Get in touch

Email [hello@beehivewebstudio.com](mailto:hello@beehivewebstudio.com) with a line or two about your site: how many turbines, which models, and what data you can export. We'll reply with next steps.

*Reports are based on the data you provide. They're not engineering advice, and any finding should be checked by a qualified engineer, with site records and inspections, before anyone acts on it.*
