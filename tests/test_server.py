import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import (
    check_orr_licence_compliance,
    check_railway_interoperability_directive,
    check_tsi_loc_pas_freight,
    check_rsl_safety_certificate,
    check_dgsa_rail_class7_class1,
    prepare_orr_inspection_pack,
    check_network_rail_capacity_access,
    ORR_LICENCE_CLASSES,
    ROGS_SAFETY_LICENCE_REQS,
    RIR_2011_REQUIREMENTS,
    ORR_14_MAJOR_ISSUES,
    NETWORK_CODE_PART_D,
)


def _call(t, **kw):
    fn = t.fn if hasattr(t, "fn") else t
    return fn(**kw)


# ──────────────────────────────────────────────────────────
# 1. check_orr_licence_compliance
# ──────────────────────────────────────────────────────────

def test_orr_freight_op_missing_licence_blocks():
    r = _call(check_orr_licence_compliance,
              operator_name="GBRf",
              licence_classes_held=["station"],
              operations=["freight_haul"])
    assert r["gaps_count"] == 1
    assert r["gaps"][0]["required_licence_class"] == "operating_freight"
    assert r["gaps"][0]["severity"] == "BLOCKING"
    assert r["compliant"] is False


def test_orr_full_licence_compliant():
    r = _call(check_orr_licence_compliance,
              operator_name="DB Cargo UK",
              licence_classes_held=["operating_freight", "light_maintenance_depot"],
              operations=["freight_haul", "operate_lmd"],
              licence_expiry_date="2030-01-01")
    assert r["gaps_count"] == 0
    assert r["compliant"] is True


def test_orr_expired_licence_flagged():
    r = _call(check_orr_licence_compliance,
              operator_name="OldCo",
              licence_classes_held=["operating_freight"],
              operations=["freight_haul"],
              licence_expiry_date="2020-01-01")
    assert r["days_to_expiry"] < 0
    assert "EXPIRED" in r["expiry_alert"]
    assert r["compliant"] is False


# ──────────────────────────────────────────────────────────
# 2. check_railway_interoperability_directive
# ──────────────────────────────────────────────────────────

def test_rir_all_attestations_missing_blocks():
    r = _call(check_railway_interoperability_directive,
              rolling_stock_id="LOC-66001")
    # Missing nobo + debo + asbo + no TSI certs => 4 findings
    assert r["findings_count"] >= 3
    assert r["ready_for_authorisation"] is False
    blocking = [f for f in r["findings"] if f["severity"] == "BLOCKING"]
    assert len(blocking) >= 2


def test_rir_full_conformity_authorises():
    r = _call(check_railway_interoperability_directive,
              rolling_stock_id="WAG-IIA-123",
              subsystem="rolling_stock",
              tsi_certificates=["TSI WAG 2014/1304 cert-001"],
              nobo_attestation=True,
              debo_attestation=True,
              asbo_csm_ra=True)
    assert r["findings_count"] == 0
    assert r["ready_for_authorisation"] is True
    assert "Authorisation for Placing in Service" in r["next_step"]


# ──────────────────────────────────────────────────────────
# 3. check_tsi_loc_pas_freight
# ──────────────────────────────────────────────────────────

def test_tsi_freight_wagon_missing_subsystems():
    r = _call(check_tsi_loc_pas_freight,
              vehicle_id="HOA-001",
              vehicle_type="freight_wagon",
              subsystems_evidenced=[],
              brake_uic_540=False)
    # Should flag all 6 wagon subsystems + brake_uic_540
    assert r["issues_count"] >= 6
    assert r["conformity_ok"] is False
    assert r["applicable_tsi"] == "TSI WAG"


def test_tsi_freight_loco_complete_passes():
    r = _call(check_tsi_loc_pas_freight,
              vehicle_id="66-001",
              vehicle_type="freight_locomotive",
              subsystems_evidenced=[
                  "structure_and_mechanical_parts",
                  "vehicle_track_interaction",
                  "braking",
                  "environmental_conditions",
                  "external_lights_horn",
                  "vehicle_diagnostic_and_recording",
                  "traction_power_supply",
                  "onboard_control_command",
              ],
              max_axleload_t=22.0,
              max_speed_kmh=120,
              brake_uic_540=True,
              etcs_baseline="Baseline 3 R2")
    assert r["issues_count"] == 0
    assert r["conformity_ok"] is True
    assert r["applicable_tsi"] == "TSI LOC&PAS + TSI CCS"


def test_tsi_axleload_over_25t_blocks():
    r = _call(check_tsi_loc_pas_freight,
              vehicle_id="HEAVY-001",
              vehicle_type="freight_wagon",
              subsystems_evidenced=[],
              max_axleload_t=26.5,
              brake_uic_540=True)
    blocking_axle = [i for i in r["issues"] if "Axleload" in i.get("issue", "")]
    assert len(blocking_axle) == 1
    assert blocking_axle[0]["severity"] == "BLOCKING"


# ──────────────────────────────────────────────────────────
# 4. check_rsl_safety_certificate
# ──────────────────────────────────────────────────────────

def test_rsl_missing_parts_blocks():
    r = _call(check_rsl_safety_certificate,
              operator_name="NewFOC",
              part_a_held=False,
              part_b_held=False)
    assert r["operating_lawfully"] is False
    codes = [f["issue"] for f in r["findings"]]
    assert any("Part A" in c for c in codes)
    assert any("Part B" in c for c in codes)


def test_rsl_valid_5yr_window_ok():
    from datetime import date as _d, timedelta
    issued = (_d.today() - timedelta(days=365)).isoformat()
    r = _call(check_rsl_safety_certificate,
              operator_name="GBRf",
              part_a_held=True,
              part_b_held=True,
              issue_date=issued,
              sms_audit_within_12mo=True,
              annual_safety_report_submitted=True)
    assert r["operating_lawfully"] is True


def test_rsl_5yr_expired():
    r = _call(check_rsl_safety_certificate,
              operator_name="StaleCo",
              part_a_held=True,
              part_b_held=True,
              issue_date="2018-01-01",
              sms_audit_within_12mo=True,
              annual_safety_report_submitted=True)
    assert "EXPIRED" in r["renewal_alert"]
    assert r["operating_lawfully"] is False


# ──────────────────────────────────────────────────────────
# 5. check_dgsa_rail_class7_class1
# ──────────────────────────────────────────────────────────

def test_dgsa_class7_high_ti_blocks():
    r = _call(check_dgsa_rail_class7_class1,
              consignment_id="C-001",
              rid_class="7",
              un_number="UN2912",
              package_type="type_a",
              transport_index_total=75.0,
              has_trem_card=True,
              has_dgsa_appointed=True)
    ti_blockers = [f for f in r["findings"] if "Transport Index" in f.get("issue", "")]
    assert len(ti_blockers) == 1
    assert ti_blockers[0]["severity"] == "BLOCKING"
    assert r["clearance_status"] == "BLOCKED_PENDING_FIXES"


def test_dgsa_class1_div_1_1_needs_esc():
    r = _call(check_dgsa_rail_class7_class1,
              consignment_id="EXP-001",
              rid_class="1",
              un_number="UN0081",
              division="1.1",
              compatibility_group="D",
              has_trem_card=True,
              has_dgsa_appointed=True,
              has_esc_certificate=False)
    esc_block = [f for f in r["findings"] if "Explosives Safety Certificate" in f.get("issue", "")]
    assert len(esc_block) == 1


def test_dgsa_class7_clean_clear():
    r = _call(check_dgsa_rail_class7_class1,
              consignment_id="C-002",
              rid_class="7",
              un_number="UN2916",
              package_type="type_b_u",
              transport_index_total=12.5,
              has_trem_card=True,
              has_dgsa_appointed=True)
    assert r["clearance_status"] == "CLEAR_TO_DESPATCH"
    assert r["findings_count"] == 0


# ──────────────────────────────────────────────────────────
# 6. prepare_orr_inspection_pack
# ──────────────────────────────────────────────────────────

def test_orr_pack_has_14_issues():
    r = _call(prepare_orr_inspection_pack,
              operator_name="Freightliner",
              inspection_date="2026-09-01",
              inspection_type="scheduled")
    assert r["major_issues_count"] == 14
    assert len(r["evidence_per_issue"]) == 14
    assert len(r["pre_visit_checklist"]) >= 5


def test_orr_pack_enforcement_risks_listed():
    r = _call(prepare_orr_inspection_pack, operator_name="DRS")
    risks = r["enforcement_risk_reference"]
    assert any("Improvement notice" in x for x in risks)
    assert any("Prohibition notice" in x for x in risks)


# ──────────────────────────────────────────────────────────
# 7. check_network_rail_capacity_access
# ──────────────────────────────────────────────────────────

def test_nr_25kv_mismatch_blocks():
    r = _call(check_network_rail_capacity_access,
              operator_name="Colas",
              slot_id="P-001",
              traction_type="diesel",
              requires_traction_current_25kv=True)
    issues = [i for i in r["issues"] if "25kV" in i.get("issue", "")]
    assert len(issues) == 1
    assert issues[0]["severity"] == "BLOCKING"
    assert r["ready_for_capacity_application"] is False


def test_nr_freight_priority_advisory():
    r = _call(check_network_rail_capacity_access,
              operator_name="GBRf",
              slot_id="GBRF-AT-99",
              origin="Felixstowe",
              destination="Hams Hall",
              traction_type="electric_25kv_ac",
              proposed_path_kind="annual_timetable",
              declared_priority="freight")
    adv = " ".join(r["advisories"])
    assert "freight" in adv.lower()
    assert r["ready_for_capacity_application"] is True


def test_nr_ready_for_application():
    r = _call(check_network_rail_capacity_access,
              operator_name="Freightliner",
              slot_id="FL-001",
              origin="London Gateway",
              destination="Trafford Park",
              traction_type="diesel",
              proposed_path_kind="annual_timetable",
              declared_priority="freight")
    assert r["issues_count"] == 0
    assert r["ready_for_capacity_application"] is True


# ──────────────────────────────────────────────────────────
# Attestation / HMAC chain
# ──────────────────────────────────────────────────────────

def test_attestation_chain_all_tools_signed():
    # Each tool must return ts + sig + issuer
    results = [
        _call(check_orr_licence_compliance, operator_name="X"),
        _call(check_railway_interoperability_directive, rolling_stock_id="X"),
        _call(check_tsi_loc_pas_freight, vehicle_id="X", brake_uic_540=True),
        _call(check_rsl_safety_certificate, operator_name="X"),
        _call(check_dgsa_rail_class7_class1, consignment_id="X"),
        _call(prepare_orr_inspection_pack, operator_name="X"),
        _call(check_network_rail_capacity_access, operator_name="X"),
    ]
    for r in results:
        assert "sig" in r
        assert "ts" in r
        assert r["issuer"] == "meok-rail-freight-uk-mcp"
        assert r["version"] == "1.0.0"


def test_attestation_signed_with_secret():
    os.environ["MEOK_HMAC_SECRET"] = "test-secret-rail"
    # Reload module so it picks up the secret
    import importlib
    import server as srv
    importlib.reload(srv)
    fn = srv.check_orr_licence_compliance
    fn = fn.fn if hasattr(fn, "fn") else fn
    r = fn(operator_name="Signed")
    assert r["sig"] != "unsigned-no-key-configured"
    assert len(r["sig"]) == 64  # sha256 hex
    # cleanup
    del os.environ["MEOK_HMAC_SECRET"]
    importlib.reload(srv)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
