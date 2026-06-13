#!/usr/bin/env python3
"""
MEOK Rail Freight UK Compliance MCP
====================================

By MEOK AI Labs · https://haulage.app · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-rail-freight-uk-mcp -->

WHAT THIS DOES
--------------
Extends MEOK from road into UK rail freight. The single biggest £ exposure
for UK rail freight operators is **ORR enforcement** (Office of Rail and
Road) + **Network Rail access denial**.

ORR powers include:
  - Improvement notices + prohibition notices (ROGS 2006)
  - Safety certificate / authorisation revocation
  - Unlimited fines (Health & Safety at Work Act 1974)
  - Director disqualification

Target operators: Freightliner, GB Railfreight (GBRf), DB Cargo UK,
Direct Rail Services (DRS), Colas Rail, Victa Westlink Rail, Mendip Rail,
plus the new entrants under Open-Access.

This MCP gives Safety Managers, Safety Verification engineers, RAIB
liaison officers and capacity planners a callable toolkit covering:

  - ORR safety + station + network licence compliance
  - Railway Interoperability Regulations 2011 + TSI conformity
  - TSI LOC&PAS + TSI WAG technical compliance for freight rolling stock
  - Railway Safety Licence (ROGS Reg 5)
  - DGSA dangerous goods (RID Class 7 radioactive + Class 1 explosives)
  - 14 Major Issues ORR inspection prep
  - Network Rail capacity allocation + train path access

TOOLS (7)
---------
- check_orr_licence_compliance(operator_data)
- check_railway_interoperability_directive(rolling_stock)
- check_tsi_loc_pas_freight(vehicle_data)
- check_rsl_safety_certificate(operator_data)
- check_dgsa_rail_class7_class1(consignment)
- prepare_orr_inspection_pack(operator_data)
- check_network_rail_capacity_access(slot)

WHY YOU PAY
-----------
One avoided ORR enforcement notice + one preserved Network Rail timetable
slot ≫ £1,999/mo Fleet. Rail is a premium niche — six operators carry
~95% of UK rail freight; each is a multi-million-£ business with bet-the-
company regulatory exposure.

PRICING
-------
Free MIT self-host · £149/mo Starter · £399/mo Pro · £1,999/mo Fleet.

REGULATORY BASIS
----------------
Railways Act 1993 (privatisation; ORR licensing powers)
Railways and Other Guided Transport Systems (Safety) Regulations 2006 (ROGS)
Railway Interoperability Regulations 2011 (RIR 2011)
TSI LOC&PAS — Locomotives & Passenger rolling stock
TSI WAG — Freight Wagons
TSI CCS — Control, Command & Signalling
COTIF — Convention concerning International Carriage by Rail
CIM — Uniform Rules concerning the Contract of International Carriage of Goods by Rail
RID — Regulations concerning the International Carriage of Dangerous Goods by Rail
Common Safety Method on Risk Evaluation and Assessment (CSM-RA, EU 402/2013 retained)
"""

from __future__ import annotations
import urllib.request as _meter_urlreq
import urllib.error as _meter_urlerr
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone, date
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-rail-freight-uk")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


# ──────────────────────────────────────────────────────────────────────
# Regulatory tables
# ──────────────────────────────────────────────────────────────────────

# ORR licence classes (Railways Act 1993, Section 8)
ORR_LICENCE_CLASSES = {
    "network": "Network Licence — held by Network Rail (infrastructure manager)",
    "station": "Station Licence — managers of major stations",
    "light_maintenance_depot": "LMD Licence — light maintenance depot operators",
    "operating_passenger": "Passenger train operator licence",
    "operating_freight": "Freight operator licence (FOC)",
    "european": "European licence — under retained EU Directive 2012/34",
}

# ROGS 2006 — Railway Safety Licence requirements (Reg 5-11)
ROGS_SAFETY_LICENCE_REQS = {
    "safety_management_system": "Documented SMS per ROGS Reg 5(2)",
    "competence_management": "Competence management system for safety-critical staff",
    "risk_assessment": "Risk assessment using CSM-RA (EU 402/2013 retained)",
    "incident_reporting": "Notify ORR of accidents per RIDDOR + ROGS Sched 2",
    "annual_safety_report": "ASR submitted to ORR within 6 months of FY end",
    "interoperability_compliance": "RIR 2011 + applicable TSIs evidenced",
    "raib_cooperation": "Cooperation with Rail Accident Investigation Branch",
}

# RIR 2011 — Railway Interoperability Regulations key elements
RIR_2011_REQUIREMENTS = {
    "essential_requirements": [
        "Safety", "Reliability and availability", "Health",
        "Environmental protection", "Technical compatibility", "Accessibility",
    ],
    "tsi_applicable": [
        "TSI LOC&PAS — Locomotives and passenger rolling stock",
        "TSI WAG — Freight wagons",
        "TSI CCS — Control Command and Signalling",
        "TSI INF — Infrastructure",
        "TSI ENE — Energy",
        "TSI OPE — Operation and traffic management",
        "TSI PRM — Persons with Reduced Mobility",
        "TSI NOI — Noise",
        "TSI SRT — Safety in Railway Tunnels",
    ],
    "conformity_assessment": "NoBo (Notified Body) + DeBo (Designated Body) + AsBo (Assessment Body)",
}

# TSI LOC&PAS subsystems for locomotives & passenger; WAG subset applies to freight wagons
TSI_LOC_PAS_FREIGHT_SUBSYSTEMS = {
    "structure_and_mechanical_parts": "Vehicle body, bogies, wheelsets",
    "vehicle_track_interaction": "Wheel profile, axleload, ride quality",
    "braking": "Service + emergency + parking brake, UIC 540 compliance",
    "passenger_related_items": "N/A for freight wagons",
    "environmental_conditions": "Climatic + altitude operating range",
    "external_lights_horn": "Headlight + marker lights + horn",
    "traction_power_supply": "Pantograph + traction converter (locos only)",
    "onboard_control_command": "ETCS / TPWS / AWS depending on routes",
    "vehicle_diagnostic_and_recording": "OTMR — on-train monitoring recorder",
}

# ROGS Reg 5 — Safety Certificate (operating on Network Rail managed network)
RSL_SAFETY_CERT_PARTS = {
    "part_a": "EU/UK-wide — operator's overarching SMS",
    "part_b": "Network-specific — Network Rail-managed infrastructure",
    "validity": "5 years maximum; renewal application 4 months prior",
    "scope_of_operations": "Categories of service, routes, rolling stock types",
}

# RID Class 7 (radioactive) + Class 1 (explosives) — key controls
RID_CLASS_7_CONTROLS = {
    "shipper_obligations": "Radioactive Material Transport Regulations + RID 1.7",
    "package_types": ["Excepted", "Industrial (IP-1/2/3)", "Type A", "Type B(U)", "Type B(M)", "Type C"],
    "transport_index": "Total TI per wagon ≤ 50; per consignment limits per RID 7.5.11",
    "criticality_safety_index": "CSI applies to fissile material",
    "emergency_response": "TREM-CARD (Transport Emergency Card) per wagon",
    "competent_authority": "ORR (radioactive transport regulator in GB)",
}

RID_CLASS_1_CONTROLS = {
    "shipper_obligations": "Explosives Regulations 2014 + RID 1.10",
    "division_assignment": "1.1 / 1.2 / 1.3 / 1.4 / 1.5 / 1.6 mass-explosion test",
    "compatibility_group": "A through S — mixed loading rules per RID 7.5.2",
    "wagon_design": "Sheeted/closed/tank — type approval per RID 6.1/6.5",
    "competent_authority": "HSE (manufacture/storage) + ORR (transport)",
    "explosives_safety_certificate": "ESC issued by HSE pre-transport for some divisions",
}

# ORR inspection — 14 Major Issues categories (ORR Inspection methodology)
ORR_14_MAJOR_ISSUES = [
    "1. Leadership and management of health and safety",
    "2. Worker engagement and consultation",
    "3. Risk assessment and management",
    "4. Competence — selection, training, certification, assessment",
    "5. Operations control and supervision",
    "6. Asset management — infrastructure, rolling stock, signalling",
    "7. Change management",
    "8. Procurement and contract management",
    "9. Emergency planning and response",
    "10. Incident investigation and learning",
    "11. Audit and review of SMS",
    "12. Interoperability and standards compliance",
    "13. Occupational health and human factors",
    "14. Public, passenger and level-crossing safety",
]

# Network Rail capacity allocation — Network Code Part D
NETWORK_CODE_PART_D = {
    "long_term_planning": "ITP — Indicative Train Plan, 5+ years",
    "annual_timetable": "ATTP — Annual Train Timetable Plan, ~1 year",
    "short_term_planning": "Spot Bids, Variations, ad-hoc paths",
    "decision_criteria": "Decision Criteria (DC) — D2.1 to D2.7 priority rules",
    "appeal": "Access Disputes Committee — independent panel",
    "freight_priority": "ORR-mandated freight criteria — minimum protection",
    "traction_current": "AC 25kV OLE or 750V DC third-rail — confirmed by NR",
}


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(
        _HMAC_SECRET.encode(),
        json.dumps(payload, sort_keys=True, default=str).encode(),
        hashlib.sha256,
    ).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _attestation(payload: dict) -> dict:
    return {**payload, "ts": _ts(), "sig": _sign(payload),
            "issuer": "meok-rail-freight-uk-mcp", "version": "1.0.0"}


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────


def _server_meter_check(api_key: str = "") -> dict:
    """Calls the live /verify endpoint for server-side metering. Fail-open."""
    try:
        data = json.dumps({"api_key": api_key, "tool": ""}).encode()
        req = _meter_urlreq.Request(_METER_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with _meter_urlreq.urlopen(req, timeout=2.5) as r:
            d = json.loads(r.read())
            if isinstance(d, dict) and "allowed" in d:
                return d
    except Exception:
        pass
    return {"allowed": True, "tier": "anonymous", "remaining": 200, "upgrade_url": "https://meok.ai/pricing"}


_METER_URL = "https://proofof.ai/verify"


@mcp.tool()
def check_orr_licence_compliance(
    operator_name: str = "",
    licence_classes_held: Optional[list] = None,
    operations: Optional[list] = None,
    licence_expiry_date: str = "",
) -> dict:
    """Check Office of Rail and Road licence compliance under Railways Act 1993.

    Args:
      licence_classes_held: list of strings from ORR_LICENCE_CLASSES keys
      operations: list of operation descriptors, e.g.
        ["freight_haul", "manage_station", "operate_lmd"]
      licence_expiry_date: ISO YYYY-MM-DD
    """
    licence_classes_held = licence_classes_held or []
    operations = operations or []
    gaps = []

    op_to_required = {
        "freight_haul": "operating_freight",
        "passenger_haul": "operating_passenger",
        "manage_station": "station",
        "operate_lmd": "light_maintenance_depot",
        "manage_network": "network",
    }
    for op in operations:
        req = op_to_required.get(op)
        if req and req not in licence_classes_held:
            gaps.append({
                "operation": op,
                "required_licence_class": req,
                "description": ORR_LICENCE_CLASSES.get(req, ""),
                "severity": "BLOCKING",
            })

    days_to_expiry = None
    expiry_alert = None
    if licence_expiry_date:
        try:
            exp = date.fromisoformat(licence_expiry_date)
            days_to_expiry = (exp - date.today()).days
            if days_to_expiry < 0:
                expiry_alert = "EXPIRED — operating without a valid licence is a criminal offence under Railways Act 1993"
            elif days_to_expiry < 180:
                expiry_alert = f"Renewal due in {days_to_expiry}d — application to ORR should be in flight 6 months pre-expiry"
        except ValueError:
            expiry_alert = "Invalid date format — use ISO YYYY-MM-DD"

    return _attestation({
        "tool": "check_orr_licence_compliance",
        "operator_name": operator_name,
        "licence_classes_held": licence_classes_held,
        "operations_declared": operations,
        "gaps_count": len(gaps),
        "gaps": gaps,
        "days_to_expiry": days_to_expiry,
        "expiry_alert": expiry_alert,
        "compliant": len(gaps) == 0 and (days_to_expiry is None or days_to_expiry >= 0),
        "reference": "Railways Act 1993 s.6-12 + ORR Licensing Policy",
    })


@mcp.tool()
def check_railway_interoperability_directive(
    rolling_stock_id: str = "",
    subsystem: str = "rolling_stock",
    tsi_certificates: Optional[list] = None,
    nobo_attestation: bool = False,
    debo_attestation: bool = False,
    asbo_csm_ra: bool = False,
) -> dict:
    """Check Railway Interoperability Regulations 2011 conformity (retained EU 2016/797).

    Args:
      subsystem: one of 'rolling_stock', 'infrastructure', 'energy', 'ccs', 'ope'
      tsi_certificates: list of TSI cert references applied
      nobo_attestation: Notified Body EC certificate of verification
      debo_attestation: Designated Body national rules attestation
      asbo_csm_ra: Assessment Body Common Safety Method - Risk Assessment report
    """
    tsi_certificates = tsi_certificates or []
    findings = []

    if not nobo_attestation:
        findings.append({
            "issue": "Missing NoBo EC certificate of verification",
            "severity": "BLOCKING",
            "reference": "RIR 2011 reg 13 + 2016/797 art 15",
        })
    if not debo_attestation:
        findings.append({
            "issue": "Missing DeBo national rules attestation",
            "severity": "BLOCKING",
            "reference": "RIR 2011 reg 14 (UK national rules)",
        })
    if not asbo_csm_ra:
        findings.append({
            "issue": "Missing AsBo CSM-RA risk assessment",
            "severity": "HIGH",
            "reference": "EU 402/2013 retained — Common Safety Method",
        })
    if not tsi_certificates:
        findings.append({
            "issue": "No TSI certificates supplied",
            "severity": "BLOCKING",
            "reference": "RIR 2011 reg 6 — TSI conformity required",
        })

    return _attestation({
        "tool": "check_railway_interoperability_directive",
        "rolling_stock_id": rolling_stock_id,
        "subsystem": subsystem,
        "tsi_certificates_supplied": tsi_certificates,
        "applicable_tsi_reference": RIR_2011_REQUIREMENTS["tsi_applicable"],
        "essential_requirements": RIR_2011_REQUIREMENTS["essential_requirements"],
        "findings_count": len(findings),
        "findings": findings,
        "ready_for_authorisation": len(findings) == 0,
        "next_step": (
            "Submit Authorisation for Placing in Service (APIS) to ORR"
            if len(findings) == 0
            else "Close out missing conformity attestations before APIS submission"
        ),
    })


@mcp.tool()
def check_tsi_loc_pas_freight(
    vehicle_id: str = "",
    vehicle_type: str = "freight_wagon",
    subsystems_evidenced: Optional[list] = None,
    max_axleload_t: float = 22.5,
    max_speed_kmh: int = 100,
    brake_uic_540: bool = False,
    etcs_baseline: str = "",
) -> dict:
    """Check Technical Specification for Interoperability — freight applicability.

    For freight wagons: primarily TSI WAG (not LOC&PAS). For freight locomotives:
    TSI LOC&PAS applies. This tool covers both.

    Args:
      vehicle_type: 'freight_wagon' / 'freight_locomotive' / 'multiple_unit_freight'
      subsystems_evidenced: list of keys from TSI_LOC_PAS_FREIGHT_SUBSYSTEMS
      max_axleload_t: max axleload — line category D = 22.5t, E = 25t
      max_speed_kmh: design max — freight typically ≤100, container ≤120
      brake_uic_540: braking conformity per UIC 540 leaflet
      etcs_baseline: ETCS Baseline 3 Release 2 expected on UK ETCS lines
    """
    subsystems_evidenced = subsystems_evidenced or []
    issues = []

    required_for_freight_wagon = [
        "structure_and_mechanical_parts",
        "vehicle_track_interaction",
        "braking",
        "environmental_conditions",
        "external_lights_horn",
        "vehicle_diagnostic_and_recording",
    ]
    if vehicle_type == "freight_locomotive":
        required_for_freight_wagon.append("traction_power_supply")
        required_for_freight_wagon.append("onboard_control_command")

    for req in required_for_freight_wagon:
        if req not in subsystems_evidenced:
            issues.append({
                "missing_subsystem": req,
                "description": TSI_LOC_PAS_FREIGHT_SUBSYSTEMS.get(req, ""),
                "severity": "HIGH",
            })

    if max_axleload_t > 25.0:
        issues.append({
            "issue": f"Axleload {max_axleload_t}t exceeds GB max route category E (25.0t)",
            "severity": "BLOCKING",
        })
    if max_speed_kmh > 160:
        issues.append({
            "issue": f"Design speed {max_speed_kmh}km/h beyond GB freight envelope",
            "severity": "HIGH",
        })
    if not brake_uic_540:
        issues.append({
            "issue": "Braking conformity to UIC 540 not evidenced",
            "severity": "BLOCKING",
            "reference": "TSI WAG braking section 4.2.4",
        })
    if vehicle_type == "freight_locomotive" and not etcs_baseline:
        issues.append({
            "issue": "ETCS baseline not declared — required for ETCS-fitted routes",
            "severity": "HIGH",
            "reference": "TSI CCS",
        })

    return _attestation({
        "tool": "check_tsi_loc_pas_freight",
        "vehicle_id": vehicle_id,
        "vehicle_type": vehicle_type,
        "applicable_tsi": "TSI WAG" if vehicle_type == "freight_wagon" else "TSI LOC&PAS + TSI CCS",
        "subsystems_evidenced": subsystems_evidenced,
        "issues_count": len(issues),
        "issues": issues,
        "conformity_ok": len(issues) == 0,
        "max_axleload_t": max_axleload_t,
        "max_speed_kmh": max_speed_kmh,
    })


@mcp.tool()
def check_rsl_safety_certificate(
    operator_name: str = "",
    part_a_held: bool = False,
    part_b_held: bool = False,
    issue_date: str = "",
    scope_of_operations: Optional[list] = None,
    sms_audit_within_12mo: bool = False,
    annual_safety_report_submitted: bool = False,
) -> dict:
    """Check ROGS Reg 5 Railway Safety Certificate (Part A + Part B).

    Operating freight on Network Rail managed infrastructure without a
    valid Safety Certificate is a criminal offence under HSWA s.33.
    """
    scope_of_operations = scope_of_operations or []
    findings = []

    if not part_a_held:
        findings.append({
            "issue": "Missing ROGS Part A (EU/UK-wide SMS attestation)",
            "severity": "BLOCKING",
            "reference": "ROGS 2006 reg 5(1)(a)",
        })
    if not part_b_held:
        findings.append({
            "issue": "Missing ROGS Part B (Network Rail managed network specific)",
            "severity": "BLOCKING",
            "reference": "ROGS 2006 reg 5(1)(b)",
        })

    days_since_issue = None
    renewal_alert = None
    if issue_date:
        try:
            issued = date.fromisoformat(issue_date)
            days_since_issue = (date.today() - issued).days
            days_to_expiry = (5 * 365) - days_since_issue
            if days_to_expiry < 0:
                renewal_alert = "EXPIRED — 5yr validity exceeded; operating illegal"
                findings.append({"issue": "Safety Certificate expired", "severity": "BLOCKING"})
            elif days_to_expiry < 120:
                renewal_alert = f"Renewal application overdue — submit to ORR within 4 months of expiry (currently {days_to_expiry}d remaining)"
                findings.append({"issue": "Renewal window opening — file with ORR", "severity": "HIGH"})
        except ValueError:
            renewal_alert = "Invalid issue date format"

    if not sms_audit_within_12mo:
        findings.append({
            "issue": "No SMS audit within last 12 months",
            "severity": "HIGH",
            "reference": "ROGS Reg 6 — SMS effectiveness",
        })
    if not annual_safety_report_submitted:
        findings.append({
            "issue": "Annual Safety Report not submitted to ORR",
            "severity": "HIGH",
            "reference": "ROGS Reg 22",
        })

    return _attestation({
        "tool": "check_rsl_safety_certificate",
        "operator_name": operator_name,
        "part_a_held": part_a_held,
        "part_b_held": part_b_held,
        "scope_of_operations": scope_of_operations,
        "days_since_issue": days_since_issue,
        "renewal_alert": renewal_alert,
        "findings_count": len(findings),
        "findings": findings,
        "operating_lawfully": len(findings) == 0,
        "rogs_reqs_reference": ROGS_SAFETY_LICENCE_REQS,
    })


@mcp.tool()
def check_dgsa_rail_class7_class1(
    consignment_id: str = "",
    rid_class: str = "7",
    un_number: str = "",
    package_type: str = "",
    transport_index_total: float = 0.0,
    has_trem_card: bool = False,
    has_esc_certificate: bool = False,
    has_dgsa_appointed: bool = False,
    division: str = "",
    compatibility_group: str = "",
) -> dict:
    """Check RID dangerous goods for rail — Class 7 (radioactive) + Class 1 (explosives).

    Args:
      rid_class: '7' for radioactive, '1' for explosives
      un_number: e.g. 'UN2912', 'UN0081'
      package_type: for Class 7 — 'excepted', 'IP-1', 'IP-2', 'IP-3', 'type_a',
                    'type_b_u', 'type_b_m', 'type_c'
      transport_index_total: sum of TI on wagon (≤ 50 per wagon limit)
      division: for Class 1 — '1.1', '1.2', '1.3', '1.4', '1.5', '1.6'
      compatibility_group: for Class 1 — 'A' through 'S'
    """
    findings = []

    if not has_dgsa_appointed:
        findings.append({
            "issue": "No DGSA (Dangerous Goods Safety Adviser) appointed",
            "severity": "BLOCKING",
            "reference": "Carriage of Dangerous Goods Regs 2009 reg 7",
        })
    if not has_trem_card:
        findings.append({
            "issue": "Missing TREM-CARD (Transport Emergency Card)",
            "severity": "BLOCKING",
            "reference": "RID 5.4.3",
        })

    if rid_class == "7":
        if not un_number.startswith("UN"):
            findings.append({"issue": "Invalid UN number for Class 7", "severity": "HIGH"})
        valid_pkg = {"excepted", "IP-1", "IP-2", "IP-3", "type_a", "type_b_u", "type_b_m", "type_c"}
        if package_type and package_type not in valid_pkg:
            findings.append({
                "issue": f"Unknown Class 7 package type '{package_type}'",
                "severity": "HIGH",
                "valid": sorted(valid_pkg),
            })
        if transport_index_total > 50.0:
            findings.append({
                "issue": f"Transport Index {transport_index_total} exceeds wagon limit 50",
                "severity": "BLOCKING",
                "reference": "RID 7.5.11",
            })
        controls_ref = RID_CLASS_7_CONTROLS

    elif rid_class == "1":
        valid_div = {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6"}
        if division and division not in valid_div:
            findings.append({
                "issue": f"Invalid Class 1 division '{division}'",
                "severity": "BLOCKING",
                "valid": sorted(valid_div),
            })
        if not compatibility_group:
            findings.append({
                "issue": "Missing Class 1 compatibility group letter",
                "severity": "BLOCKING",
                "reference": "RID 7.5.2 — mixed loading",
            })
        if division in {"1.1", "1.2", "1.3"} and not has_esc_certificate:
            findings.append({
                "issue": "Class 1 division 1.1/1.2/1.3 requires HSE Explosives Safety Certificate",
                "severity": "BLOCKING",
                "reference": "Explosives Regulations 2014",
            })
        controls_ref = RID_CLASS_1_CONTROLS
    else:
        findings.append({
            "issue": f"This tool covers Class 7 + Class 1; '{rid_class}' not handled here",
            "severity": "INFO",
        })
        controls_ref = {}

    return _attestation({
        "tool": "check_dgsa_rail_class7_class1",
        "consignment_id": consignment_id,
        "rid_class": rid_class,
        "un_number": un_number,
        "findings_count": len(findings),
        "findings": findings,
        "clearance_status": "CLEAR_TO_DESPATCH" if len(findings) == 0 else "BLOCKED_PENDING_FIXES",
        "regulatory_controls_reference": controls_ref,
    })


@mcp.tool()
def prepare_orr_inspection_pack(
    operator_name: str = "",
    inspection_date: str = "",
    inspection_type: str = "scheduled",
    operations_in_scope: Optional[list] = None,
) -> dict:
    """Prepare an ORR inspection evidence pack against the 14 Major Issues.

    Args:
      inspection_type: 'scheduled' / 'reactive' / 'post-accident'
    """
    operations_in_scope = operations_in_scope or []

    evidence_per_issue = [
        {"issue": ORR_14_MAJOR_ISSUES[0],
         "evidence": ["Board safety policy", "TM/Safety Director appointment letter", "Safety leadership cascade"]},
        {"issue": ORR_14_MAJOR_ISSUES[1],
         "evidence": ["Safety reps election + minutes", "JSC minutes last 12mo", "Worker engagement KPIs"]},
        {"issue": ORR_14_MAJOR_ISSUES[2],
         "evidence": ["CSM-RA assessments per change", "Hazard log", "Risk register signed off"]},
        {"issue": ORR_14_MAJOR_ISSUES[3],
         "evidence": ["Driver Safety Critical Competence records", "PTS — Personal Track Safety certs",
                     "Periodic re-competence + assessment evidence"]},
        {"issue": ORR_14_MAJOR_ISSUES[4],
         "evidence": ["Rule book compliance audits", "Supervisor visits log", "SPAD investigation reports"]},
        {"issue": ORR_14_MAJOR_ISSUES[5],
         "evidence": ["Rolling stock maintenance plan + records", "WMR vehicle records",
                     "Brake test data", "Wheelset profile data"]},
        {"issue": ORR_14_MAJOR_ISSUES[6],
         "evidence": ["Change control SOP", "CSM-RA on changes", "Approved change log"]},
        {"issue": ORR_14_MAJOR_ISSUES[7],
         "evidence": ["Supplier safety audits", "Contractor competence checks", "Procurement spec library"]},
        {"issue": ORR_14_MAJOR_ISSUES[8],
         "evidence": ["Emergency plan", "Joint exercise with NR + BTP", "Derailment + spillage response sheets"]},
        {"issue": ORR_14_MAJOR_ISSUES[9],
         "evidence": ["RAIB notification log", "Internal investigation reports last 12mo",
                     "Learning + dissemination evidence"]},
        {"issue": ORR_14_MAJOR_ISSUES[10],
         "evidence": ["Annual SMS audit", "Internal audit programme", "Audit closure tracker"]},
        {"issue": ORR_14_MAJOR_ISSUES[11],
         "evidence": ["TSI declarations of conformity", "APIS letters", "RIR 2011 reg 13 evidence"]},
        {"issue": ORR_14_MAJOR_ISSUES[12],
         "evidence": ["Occupational health programme", "Fatigue risk management",
                     "Human factors in incident reviews"]},
        {"issue": ORR_14_MAJOR_ISSUES[13],
         "evidence": ["Level crossing risk assessments", "Public safety at depots",
                     "Customer/visitor safety at sidings"]},
    ]

    return _attestation({
        "tool": "prepare_orr_inspection_pack",
        "operator_name": operator_name,
        "inspection_date": inspection_date,
        "inspection_type": inspection_type,
        "operations_in_scope": operations_in_scope,
        "major_issues_count": len(ORR_14_MAJOR_ISSUES),
        "evidence_per_issue": evidence_per_issue,
        "pre_visit_checklist": [
            "Confirm ORR Inspector name + grade",
            "Confirm inspection scope letter received",
            "Brief Accountable Manager + named TM",
            "Pre-walk inspection site + remove obvious hazards",
            "Verify SMS document control — current revisions only",
            "Cancel non-essential operational activity day-of-visit",
            "Prepare meeting room + projector + printed evidence",
        ],
        "enforcement_risk_reference": [
            "Improvement notice (HSWA s.21)",
            "Prohibition notice (HSWA s.22)",
            "Unlimited fines (Magistrates / Crown Court)",
            "Director disqualification (Co Directors Disqualification Act 1986)",
        ],
    })


@mcp.tool()
def check_network_rail_capacity_access(
    operator_name: str = "",
    slot_id: str = "",
    origin: str = "",
    destination: str = "",
    proposed_path_kind: str = "annual_timetable",
    traction_type: str = "diesel",
    requires_etcs: bool = False,
    requires_traction_current_25kv: bool = False,
    requires_third_rail_750v: bool = False,
    declared_priority: str = "freight",
) -> dict:
    """Check Network Rail capacity allocation + train path access under Network Code Part D.

    Args:
      proposed_path_kind: 'long_term_planning' / 'annual_timetable' / 'short_term_planning' / 'spot_bid'
      traction_type: 'diesel' / 'electric_25kv_ac' / 'electric_750v_dc' / 'bi_mode' / 'tri_mode'
      declared_priority: 'freight' / 'passenger' / 'maintenance' / 'engineering'
    """
    issues = []
    advisories = []

    valid_path = set(NETWORK_CODE_PART_D.keys()) | {"spot_bid", "annual_timetable", "long_term_planning",
                                                     "short_term_planning"}
    if proposed_path_kind not in valid_path:
        issues.append({
            "issue": f"Unknown path kind '{proposed_path_kind}'",
            "severity": "HIGH",
        })

    if requires_traction_current_25kv and traction_type not in {"electric_25kv_ac", "bi_mode", "tri_mode"}:
        issues.append({
            "issue": "25kV OLE requested but traction type cannot use it",
            "severity": "BLOCKING",
        })
    if requires_third_rail_750v and traction_type not in {"electric_750v_dc", "bi_mode", "tri_mode"}:
        issues.append({
            "issue": "750V DC third-rail requested but traction type cannot use it",
            "severity": "BLOCKING",
        })

    if requires_etcs:
        advisories.append("Confirm ETCS Baseline 3 Release 2 fitted + driver L1/L2 competence per route")

    if declared_priority == "freight":
        advisories.append("ORR freight priority criteria apply — Decision Criterion DC2.4 (freight access protection)")

    if proposed_path_kind in {"annual_timetable", "spot_bid"}:
        advisories.append(
            f"For {proposed_path_kind}: submit via VSTP/SBP system to Network Rail with full timing data"
        )

    return _attestation({
        "tool": "check_network_rail_capacity_access",
        "operator_name": operator_name,
        "slot_id": slot_id,
        "origin": origin,
        "destination": destination,
        "proposed_path_kind": proposed_path_kind,
        "traction_type": traction_type,
        "declared_priority": declared_priority,
        "issues_count": len(issues),
        "issues": issues,
        "advisories": advisories,
        "ready_for_capacity_application": len(issues) == 0,
        "network_code_reference": NETWORK_CODE_PART_D,
        "appeal_route": "Access Disputes Committee — adc-uk.info",
    })


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
