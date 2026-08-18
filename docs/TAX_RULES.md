# Determination rule set

Every rule is a pure function of the **fact base** (entity graph + K-1/K-3 data + prior
year) and returns zero or more `Determination` records. Each determination carries an
authority citation, a confidence, and the facts that triggered it. Rules are registered
per tax year.

## Fact base inputs

| Fact | Source |
|---|---|
| Entity type, jurisdiction, tax classification | Entity record (preparer-confirmed) |
| Ownership %, capital vs profits, chain to ultimate owner | Ownership edges |
| ECI / FDAP split, US-source character | K-1 boxes 1–3, 11, 20; K-3 Parts II–IV |
| §1446 withholding | Form 8805, K-1 box 15 code O |
| Property situs states | K-1 state supplements, syndicator property schedule |
| Dispositions | K-1 box 9a/10, 8288-A, §1446(f) statements |
| Carryforwards | Prior-year return + workpapers |

## Federal rules

### R-1120F-ECI — Foreign corporation with ECI
**Trigger:** a non-U.S. corporation is allocated income from a U.S. partnership engaged in
a U.S. trade or business.
**Determination:** Form 1120-F required.
**Authority:** IRC §882(a); §875(1) (partner deemed engaged in the partnership's trade or
business); §897(a) and §1.897-1 (USRPI gain treated as ECI); Reg. §1.6012-2(g).
**Note:** rental income from U.S. real property held through an operating multifamily
partnership is virtually always ECI; the passive-investor posture of the *ultimate* owner
does not change the character at the partnership level.

### R-1120F-PROTECTIVE — Protective return
**Trigger:** foreign corporation with a U.S. partnership interest but no current-year ECI
allocated (or a good-faith position that no ECI exists).
**Determination:** file a protective Form 1120-F.
**Authority:** Reg. §1.882-4(a)(3)(vi).
**Why it matters:** without a timely filed return, §882(c)(2) denies **all** deductions
and credits — the foreign corporation is taxed on gross ECI. A protective return costs a
few hundred dollars; missing one can cost a multiple of the investment's income.

### R-871D-ELECTION — Net election
**Trigger:** U.S. real property income that would otherwise be gross-basis FDAP.
**Determination:** evaluate §882(d)/§871(d) election to treat income as ECI.
**Authority:** IRC §871(d), §882(d); Reg. §1.871-10.
**Note:** once made the election is binding for later years unless revoked with consent.
Check prior-year returns for an existing election before considering a new one.

### R-BRANCH-PROFITS — Branch profits tax
**Trigger:** foreign corporation with ECI and a dividend-equivalent amount.
**Determination:** Form 1120-F Schedule I / §884 computation.
**Authority:** IRC §884(a); Canada–U.S. Treaty Art. X(6) reduces the rate to **5%**, and
Art. X(7)/XXIX-A limitation-on-benefits must be satisfied.
**Note:** the treaty rate is a claimed position, not a default. It requires a qualifying
person analysis, and it belongs on Form 8833 where the position is treaty-based.

### R-8833-TREATY — Treaty-based return position disclosure
**Trigger:** any treaty article relied on to reduce U.S. tax.
**Determination:** Form 8833 attached to the 1120-F.
**Authority:** IRC §6114; Reg. §301.6114-1. **$1,000 penalty per failure** for a
corporation (§6712).

### R-5472-REPORTABLE — 25% foreign-owned U.S. entity
**Trigger:** a U.S. corporation (or U.S. disregarded entity) that is 25% foreign-owned and
had a reportable transaction with a related party.
**Determination:** Form 5472 with a pro-forma 1120 where the filer is a DRE.
**Authority:** IRC §6038A; Reg. §1.6038A-2, §301.7701-2(c)(2)(vi).
**Penalty:** $25,000 per form, per year.

### R-8865-CFP — U.S. person and a foreign partnership
**Trigger:** a U.S. person controls (>50%) or holds a 10%+ interest in a controlled foreign
partnership.
**Determination:** Form 8865, category determined by ownership and acquisition events.
**Authority:** IRC §6038, §6038B, §6046A.
**Applicability here:** this rule fires only if the structure contains a U.S. person above
a *non-U.S.* partnership. A Canadian **corporation** above a **U.S.** LP does not trigger
8865 — the mirror-image obligation is the U.S. partnership's own Form 1065 and its
§1446 withholding. The engagement asks about 8865 explicitly, so the engine evaluates it
and records an explicit *not required, because* determination rather than silence.

### R-1446-WITHHOLDING — ECTI withholding credit
**Trigger:** foreign partner allocated ECTI.
**Determination:** reconcile Forms 8805 to K-1 box 15 code O; claim the credit on the
1120-F.
**Authority:** IRC §1446; Reg. §1.1446-3; Forms 8804/8805/8813.
**Common defect:** the syndicator withholds at 21% but issues the 8805 to the *wrong*
tier of the structure. If the 8805 payee TIN does not match the filing entity, the credit
is at risk and must be corrected with the partnership before filing.

### R-1446F-TRANSFER — Transfer of a partnership interest
**Trigger:** disposition of an interest in a partnership engaged in a U.S. trade or
business.
**Determination:** 10% transferee withholding; Form 8288/8288-A; transferor claims credit.
**Authority:** IRC §1446(f); Reg. §1.1446(f)-2.

### R-FIRPTA-DISP — Disposition of a U.S. real property interest
**Trigger:** the partnership disposes of U.S. real property; §897 gain flows to the
foreign partner.
**Determination:** 8288-A credit; ECI treatment; capital gain character.
**Authority:** IRC §897, §1445; §1.1445-5(c).

### R-163J-EBIE — Excess business interest expense
**Trigger:** K-1 box 13 code K.
**Determination:** track EBIE carryforward per partnership; Form 8990 where applicable.
**Authority:** IRC §163(j); Reg. §1.163(j)-6 (partnership-level 11-step allocation).
**Note:** EBIE is suspended at the partner level and released only by excess taxable
income from the *same* partnership. It is per-partnership, never pooled.

### R-BASIS-LIMIT — Loss limitation stack
**Trigger:** allocated loss.
**Determination:** apply the limitations in order — **§704(d) outside basis → §465 at-risk
→ §469 passive activity → §461(l) excess business loss**.
**Authority:** IRC §704(d), §465, §469, §461(l).
**Why the order matters:** applying §469 before §704(d) produces a suspended loss in the
wrong bucket with the wrong release condition, and the error compounds for the life of
the investment. Real-estate syndications with nonrecourse debt make the at-risk step live:
qualified nonrecourse financing under §465(b)(6) is at-risk, ordinary nonrecourse is not.

### R-EXTENSION — Extension of time to file
**Trigger:** every return the engine determines.
**Determination:** Form 7004; **Form 1120-F for a foreign corporation with no U.S. office
is due the 15th day of the 6th month** (June 15 for a calendar year), extendable 6 months.
**Authority:** Reg. §1.6072-2(b); Form 7004 instructions.
**Practical driver:** syndicator K-1s routinely arrive after the original due date. The
engine's default posture is **extend everything**, then file.

## State rules

Multifamily syndications concentrate in TX, GA, FL, NC, AZ, TN, OH. The state engine keys
off property situs, not the partnership's formation state.

| State | Rule |
|---|---|
| TX | No income tax. **Franchise (margin) tax** applies to entities with nexus; a non-U.S. corporation with a Texas-situs partnership interest can have a filing obligation. Passive-entity and no-tax-due thresholds evaluated. |
| FL | No individual income tax; **corporate income tax applies** to a foreign corporation with Florida ECI. F-1120. |
| GA | Nonresident withholding (O.C.G.A. §48-7-129) or composite; 600S/600 as applicable |
| NC | Nonresident withholding; composite election available |
| AZ | Nonresident composite (Form 140NR / 120S sched) |
| TN | Franchise & excise tax — applies to LPs; commonly missed |
| OH | Pass-through entity withholding (IT 4708 / IT 1140) |

**Composite-vs-separate is a decision, not a default.** If the syndicator made a composite
election, the partner may be relieved of a filing — or may be *worse off* because the
composite rate ignores the partner's other state activity. The engine surfaces the choice
with both outcomes computed; it does not pick silently.

## Cross-border advisory flags (out of U.S. filing scope, into the memo)

These are not filed by this engagement. They are surfaced because failing to mention them
is the difference between a preparer and an advisor.

- **T1134** — Canadian holdco with a foreign affiliate; U.S. LP interests can require it.
- **T1135** — foreign property > CAD 100,000.
- **Foreign tax credit / surplus accounts** — U.S. tax paid must be usable in Canada;
  timing mismatches between the two systems create permanent double tax if unplanned.
- **FAPI** — generally not triggered by active rental businesses, but the analysis should
  be stated, not assumed.
- **Treaty Art. XXIX-A LOB** — the holdcos must qualify for treaty benefits to claim them.
