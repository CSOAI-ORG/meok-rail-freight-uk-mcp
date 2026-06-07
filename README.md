<!-- mcp-name: io.github.CSOAI-ORG/meok-rail-freight-uk-mcp -->
[![MCP Scorecard: 84/100](https://img.shields.io/badge/proofof.ai-84%2F100-5b21b6)](https://proofof.ai/scorecard/meok-rail-freight-uk-mcp.html)

# meok-rail-freight-uk-mcp

> UK rail freight compliance — ORR licensing, ROGS safety certificate, Railway Interoperability Regulations 2011, TSI LOC&PAS / WAG, RID dangerous goods, ORR 14 Major Issues inspection prep, Network Rail capacity access. By **MEOK AI Labs**.

## Why this exists

UK rail freight's single biggest £ exposure is **ORR enforcement** (Office of Rail and Road) plus **Network Rail capacity denial**. ORR powers include:

- Improvement notices + prohibition notices (ROGS 2006 / HSWA 1974)
- Safety certificate + authorisation revocation
- Unlimited fines (Health & Safety at Work Act 1974)
- Director disqualification
- Operating-without-licence is a criminal offence under Railways Act 1993

Target operators: Freightliner, GB Railfreight (GBRf), DB Cargo UK, Direct Rail Services (DRS), Colas Rail, Victa Westlink Rail, Mendip Rail, plus new Open-Access entrants. Network Rail is the upstream infrastructure manager. ORR is the regulator.

This MCP extends MEOK's haulage suite from road into rail. It gives Safety Managers, Verification engineers, RAIB liaison officers and capacity planners the callable toolkit to **stay licensed and keep paths**.

## Install

```bash
pip install meok-rail-freight-uk-mcp
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "rail-freight-uk": {
      "command": "meok-rail-freight-uk-mcp"
    }
  }
}
```

## Tools (7)

| Tool | Use case |
|------|----------|
| `check_orr_licence_compliance` | Network/Station/Operating licence held vs operations declared |
| `check_railway_interoperability_directive` | RIR 2011 conformity — NoBo + DeBo + AsBo CSM-RA |
| `check_tsi_loc_pas_freight` | TSI LOC&PAS + TSI WAG subsystem evidence |
| `check_rsl_safety_certificate` | ROGS Reg 5 Part A + Part B Safety Certificate |
| `check_dgsa_rail_class7_class1` | RID Class 7 (radioactive) + Class 1 (explosives) |
| `prepare_orr_inspection_pack` | Evidence pack against ORR's 14 Major Issues |
| `check_network_rail_capacity_access` | Capacity allocation + train path under Network Code Part D |

## Pricing

- **Free** — MIT self-host
- **Starter** — £149/mo
- **Pro** — £399/mo (multi-operator)
- **Fleet** — £1,999/mo (FOC-scale + capacity planner integration)

Rail = premium niche. Six operators carry ~95% of UK rail freight, each a multi-million-£ business with bet-the-company regulatory exposure. One avoided ORR enforcement notice + one preserved Network Rail timetable slot easily covers the year.

## Regulatory basis

- **Railways Act 1993** — ORR licensing powers
- **Railways and Other Guided Transport Systems (Safety) Regulations 2006 (ROGS)** — safety certificate, SMS
- **Railway Interoperability Regulations 2011 (RIR 2011)** — TSI conformity (retained EU 2016/797)
- **TSI LOC&PAS** — Locomotives & Passenger rolling stock
- **TSI WAG** — Freight Wagons
- **TSI CCS** — Control, Command & Signalling
- **COTIF / CIM** — Convention concerning International Carriage by Rail
- **RID** — Regulations concerning International Carriage of Dangerous Goods by Rail
- **CSM-RA (EU 402/2013 retained)** — Common Safety Method on Risk Evaluation
- **Network Code Part D** — Network Rail capacity allocation, Decision Criteria DC2.1–2.7

## Sign your responses

```bash
export MEOK_HMAC_SECRET="your-secret"
meok-rail-freight-uk-mcp
```

## License

MIT (c) 2026 Nicholas Templeman / MEOK AI Labs · [haulage.app](https://haulage.app)


<!-- GEO-FOOTER:v1 -->

---

### Part of the MEOK constellation

This MCP is one node in a connected ecosystem built by **MEOK AI LABS** around a single
sovereign AI core — governed agents with a hash-chained audit trail, mapped to the CSOAI
compliance charter.

- 🌐 The whole map: **<https://meok.ai/constellation>**
- 🛡️ AI governance & certification: **<https://councilof.ai>** · **<https://csoai.org>**
- ✅ Verify any signed report: **<https://meok.ai/verify>**
