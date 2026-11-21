---
name: pro-ticket
description: Create a procurement (PRO) Jira ticket, or flesh out an existing one, for hardware Brandon wants bought (memory, drives, NICs, a server). Reads the target host's specs, researches OEM and third-party prices with sources, fills every engineering field including the ones that only exist after creation (Acceptance Criteria, Site, Lab / Location, dates, priority, power), comments a price comparison, and lists the choices for Brandon to check. Use when asked to "make a PRO ticket for X", "open a procurement request", or "flesh out PRO-<n>".
---

# Procurement ticket

Every Jira write posts as Brandon. Keep the text factual, with numbers and sources, and don't write anything you can't back up.

## Config

Read `pro-ticket.local.yaml` next to this file. It's gitignored because it holds the project's field IDs, option IDs and site names. Copy it from `pro-ticket.local.yaml.example`. If it's missing, say so and stop: don't guess field IDs.

- `project`, `issue_types`: the procurement project and its issue types. Hardware is the usual one.
- `reference_ticket`: a filed ticket to read first. Match its depth, structure and tone.
- `fields.create`: fields on the create screen. `fields.edit`: fields that **only exist after creation**, and that the create call rejects. `procurement_only`: fields that procurement fills in. Never set those.
- `options`: the option ID for each select value. `defaults`: values to use unless Brandon says otherwise.
- `lead_weeks`, `padding`, `fiscal_year_start_month`, `requestor`, `tz`.

If a create or update is rejected for a field ("not on the appropriate screen", or an unknown option), read `GET issue/createmeta/<project>/issuetypes/<id>` (for a create) or `GET issue/<key>/editmeta` (for an update). Fix the call, and fix the local yaml so the next run doesn't hit the same error.

## Modes

- **New**, "make a PRO ticket for <thing>": follow every step.
- **Flesh out**, "flesh out <KEY>": read the ticket with every field in the config. Fill each empty field. Rewrite a filled field only when it's a placeholder or wrong, and quote its old text in the report. Then add the price comparison comment if the ticket doesn't have one.
- For a Cloud or Service procurement, read that type's createmeta first: its fields differ from the hardware type.

## Steps

1. **Gather the facts.** Find out what's being bought, for which host, why, and who asked. Read the host itself when you can reach it (`dmidecode -t memory`, `lscpu`, `free -g`, `lsblk`, `lspci`, the BMC). Read the vendor's spec pages for the population rules (e.g. channels per CPU, the maximum speed at 1 DIMM per channel), and any tickets that link to the request. Mark what you couldn't confirm as "to confirm with <command> before ordering". Don't present a guess as a fact.
2. **Research prices.** Find at least two sources for each of:
   - the **OEM-branded part** (the server vendor's own part number);
   - an **equivalent third-party part** with the same spec (capacity, ranks, speed, ECC/registered), and evidence that it works in this exact model (the vendor's compatibility list or the module maker's configurator).
   Record each price with its URL, the date it was listed, and whether it's a list price or a sale price. Prefer current listings, and flag any listing that's old.
3. **Pick the part and the estimate.** The order names the third-party part, and the OEM part goes in as the fallback "if vendor-branded parts are required". Brandon may want the OEM part, or a deliberately padded estimate. If he hasn't said, ask him before the create. Estimate = qty × the upper end of the third-party unit price, + `padding` (tax, shipping, price movement), rounded up to a round number. Show the arithmetic.
4. **Create** the ticket with the type from `issue_types`, plus:
   - **summary**: `<what> for <host> (<model>): <qty>x <spec> (<total>) so it can <outcome>`;
   - **description**: start with `Related: <ticket> (<one line>)`. Then the request in one paragraph. Then "Current state (read on the host <date>):" as bullets with the facts from step 1. Then any dependencies (what has to move or happen first, and who owns it). Then a line or two of context;
   - every `fields.create` field the type requires, plus Estimated Cost and the Requestor (`requestor`, unless someone else asked).

   Put the rich-text fields in the update (step 5), not in the create. Jira wants ADF for those, and the update is where it's easy to get right.
5. **Update** in one call. Set every rich-text field and every `fields.edit` field:
   - **Requested Configuration**: the platform and host. Then the exact part number and quantity, with "all N identical, from one lot if possible". Then the population rules with their source, and the total. Then what happens to the parts being replaced (removed, not mixed in, kept as spares). Then the OEM fallback part, an optional bigger "Option B", and the estimate with its arithmetic.
   - **What does it enable?**: one paragraph naming the system and the teams it serves, then 2 or 3 bullets with numbers (e.g. "8x today's memory bandwidth").
   - **What happens if we don't buy it?**: the concrete cost of waiting: what stays idle, which single point of failure stays, what older hardware we keep leaning on.
   - **Why can't existing hardware do it?**: bullets, one per alternative ruled out, with the reason (each other host's role, spare parts in the lab, the age of the other options).
   - **Acceptance Criteria**: numbered lines for (1) received at the site, all identical, naming the part (or the fallback); (2) installed per the population rules, with the old parts kept as spares; (3) the BIOS or BMC shows the new total, healthy and at the expected speed, with no errors after POST; (4) the OS sees it, with the exact command and the expected number; (5) a burn-in period (7 days by default) with no uncorrectable or repeating correctable errors.
   - **Site** and **Lab / Location** (`<defaults.lab_name>: <host> (<model>), <IP>`; for a host in another lab, name that lab and pick its Site); **Team / Project** and **components** from `defaults`; **priority** from `defaults` unless Brandon gave one.
   - **Requested On** = today (in `tz`). **Required By** = the Requested Delivery Date = about `lead_weeks` out, on a weekday.
   - **Estimated Avg. Power (kW)**: the average extra draw this adds, from a datasheet or a typical figure (e.g. about 5 W per DDR5 RDIMM). For a whole server, use its typical draw, not the PSU rating.
   - **Customer Impact**: `defaults.customer_impact` for internal infrastructure, otherwise one sentence naming the customer-facing effect.
   - **Fiscal Year / Quarter**: only when `fiscal_year_start_month` is set (then use the quarter that holds Required By). Otherwise leave them empty and ask.

   Rich-text fields (the configuration, the three justification fields, Acceptance Criteria, Customer Impact) are ADF in Jira's REST v3. Send plain text only through a tool that says it converts plain strings to ADF. Otherwise build the ADF yourself: one paragraph per block, a `hardBreak` between numbered lines, and `bulletList` for bullets.
6. **Comment** the price comparison: `Price comparison for <qty>x <spec> (public listings, <date>, no vendor quote yet):`. Add one bullet per part: part number, spec, the unit price at each source (with the listing date when it's not current), and the total for the full quantity. Then one paragraph on what the OEM premium buys (support coverage, and whether the BMC flags or vendor support rejects third-party parts). Then one line tying it to the Estimated Cost. If you change the estimate later, add a comment that says what it changed from and why.
7. **Don't** transition the ticket (procurement owns its workflow), set any `procurement_only` field, set Scrum Team, or change the assignee unless Brandon names one.

## Report

Reply with the ticket link, then a list of every choice Brandon should check:

- **Part**: third-party or OEM, and the fallback.
- **Quantity and total**, and whether "Option B" is worth it.
- **Estimated Cost**: the arithmetic and the padding.
- **Dates**: Requested On, Required By.
- **Selects**: Product Team, Initiative Area, Site, Team / Project, component, priority.
- **Power**: the figure and its basis.
- **Assignee**: usually whoever receives and installs the part. It's left empty unless he names someone.
- **Fiscal Year / Quarter**: if they're still empty.
- **To confirm**: every fact you couldn't verify on the host.

Give the price sources as links.
