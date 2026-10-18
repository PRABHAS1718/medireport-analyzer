"""Unit and integration tests for conversational medical memory & context endpoints.

Tests rule-based candidate fact extraction, ambiguity & family member detection,
memory preference toggles, confirmation flow, corrections, soft-deletion, and zero-trust cross-user isolation.
"""

import pytest
from httpx import AsyncClient


async def create_user_and_patient(client: AsyncClient, email: str) -> tuple[str, str]:
    """Helper to create a user and patient profile, returning (token, patient_id)."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "preferred_language": "en"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pat_res = await client.post(
        "/api/v1/patients",
        json={"display_name": "Context Patient", "sex": "female", "blood_group": "A+"},
        headers=headers,
    )
    patient_id = pat_res.json()["id"]
    return token, patient_id


@pytest.mark.asyncio
async def test_context_capture_medication(client: AsyncClient):
    """Test capturing a direct medication statement with dosage."""
    token, patient_id = await create_user_and_patient(client, "ctx_med@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I take Metformin 500 mg daily for blood sugar."},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["memory_enabled"] is True
    assert data["status"] == "captured"
    assert data["facts_captured"] >= 1
    
    fact = data["facts"][0]
    assert fact["fact_type"] == "medication"
    assert "Metformin" in fact["normalized_fact"]["medication_name"]
    assert fact["confidence"] >= 0.9
    assert fact["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_context_capture_uncertainty(client: AsyncClient):
    """Test capturing an uncertain statement flags needs_confirmation and lower confidence."""
    token, patient_id = await create_user_and_patient(client, "ctx_uncertain@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I think maybe I took some Paracetamol yesterday."},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["facts_captured"] >= 1
    fact = data["facts"][0]
    assert fact["needs_confirmation"] is True
    assert fact["confidence"] <= 0.70


@pytest.mark.asyncio
async def test_context_capture_family_reference(client: AsyncClient):
    """Section 20 safety rule: References to family members must flag subject warning and require confirmation."""
    token, patient_id = await create_user_and_patient(client, "ctx_family@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "My father was diagnosed with diabetes in 2018."},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["facts_captured"] >= 1
    fact = data["facts"][0]
    assert fact["needs_confirmation"] is True
    assert fact["confidence"] <= 0.50
    assert "family member" in fact["normalized_fact"].get("subject_warning", "").lower()


@pytest.mark.asyncio
async def test_context_memory_disabled_toggle(client: AsyncClient):
    """Test that toggling persistent memory off disables new fact captures."""
    token, patient_id = await create_user_and_patient(client, "ctx_toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial settings
    get_res = await client.get(f"/api/v1/patients/{patient_id}/memory-settings", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["memory_enabled"] is True

    # Disable memory
    patch_res = await client.patch(
        f"/api/v1/patients/{patient_id}/memory-settings",
        json={"memory_enabled": False},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["memory_enabled"] is False

    # Attempt capture while disabled
    cap_res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I take Aspirin 100 mg daily."},
        headers=headers,
    )
    assert cap_res.status_code == 201
    assert cap_res.json()["status"] == "disabled"
    assert cap_res.json()["facts_captured"] == 0


@pytest.mark.asyncio
async def test_context_manual_create_and_list(client: AsyncClient):
    """Test manual context fact creation and filtered listing."""
    token, patient_id = await create_user_and_patient(client, "ctx_manual@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Manually create allergy fact
    payload = {
        "fact_type": "allergy",
        "original_statement_excerpt": "Severe allergy to penicillin",
        "normalized_fact": {"allergen": "Penicillin", "reaction": "Anaphylaxis"},
        "source_type": "manual",
        "effective_date": "2015",
        "record_status": "user_confirmed",
        "confidence": 1.0,
        "needs_confirmation": False,
    }
    create_res = await client.post(f"/api/v1/patients/{patient_id}/context", json=payload, headers=headers)
    assert create_res.status_code == 201
    fact_id = create_res.json()["id"]

    # List facts with filtering
    list_res = await client.get(f"/api/v1/patients/{patient_id}/context?fact_type=allergy", headers=headers)
    assert list_res.status_code == 200
    facts = list_res.json()
    assert len(facts) == 1
    assert facts[0]["id"] == fact_id
    assert facts[0]["fact_type"] == "allergy"


@pytest.mark.asyncio
async def test_confirm_candidate_fact(client: AsyncClient):
    """Test promoting an ambiguous or unconfirmed fact to user_confirmed."""
    token, patient_id = await create_user_and_patient(client, "ctx_confirm@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Capture uncertain fact
    cap_res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I think maybe I took Amoxicillin 250 mg."},
        headers=headers,
    )
    fact_id = cap_res.json()["facts"][0]["id"]
    assert cap_res.json()["facts"][0]["needs_confirmation"] is True

    # Confirm fact
    confirm_res = await client.post(f"/api/v1/patients/{patient_id}/context/{fact_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    confirmed_fact = confirm_res.json()
    assert confirmed_fact["record_status"] == "user_confirmed"
    assert confirmed_fact["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_update_and_delete_context_fact(client: AsyncClient):
    """Test updating/correcting a fact and soft-deleting it."""
    token, patient_id = await create_user_and_patient(client, "ctx_edit@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Capture fact
    cap_res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I have mild headache since yesterday."},
        headers=headers,
    )
    fact_id = cap_res.json()["facts"][0]["id"]

    # Correct/update fact
    patch_res = await client.patch(
        f"/api/v1/patients/{patient_id}/context/{fact_id}",
        json={"confidence": 0.99, "effective_date": "2026-10-17"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["confidence"] == 0.99
    assert patch_res.json()["effective_date"] == "2026-10-17"

    # Soft-delete fact
    del_res = await client.delete(f"/api/v1/patients/{patient_id}/context/{fact_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify fact is excluded from active context list
    list_res = await client.get(f"/api/v1/patients/{patient_id}/context", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_cross_user_isolation_on_context_memory(client: AsyncClient):
    """MANDATORY SECURITY GATE: User B cannot capture, view, confirm, or edit User A's context memory."""
    token_a, patient_a = await create_user_and_patient(client, "ctx_owner@example.com")
    token_b, _ = await create_user_and_patient(client, "ctx_attacker@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A captures a fact
    cap_res = await client.post(
        f"/api/v1/patients/{patient_a}/context/capture",
        json={"statement": "I take Metformin 500 mg daily."},
        headers=headers_a,
    )
    fact_id = cap_res.json()["facts"][0]["id"]

    # User B attempts to read User A's context facts
    res_list = await client.get(f"/api/v1/patients/{patient_a}/context", headers=headers_b)
    assert res_list.status_code == 404

    # User B attempts to capture fact into User A's profile
    res_cap = await client.post(
        f"/api/v1/patients/{patient_a}/context/capture",
        json={"statement": "Malicious statement"},
        headers=headers_b,
    )
    assert res_cap.status_code == 404

    # User B attempts to confirm User A's fact
    res_conf = await client.post(f"/api/v1/patients/{patient_a}/context/{fact_id}/confirm", headers=headers_b)
    assert res_conf.status_code == 404

    # User B attempts to update User A's fact
    res_patch = await client.patch(
        f"/api/v1/patients/{patient_a}/context/{fact_id}",
        json={"confidence": 0.1},
        headers=headers_b,
    )
    assert res_patch.status_code == 404

    # User B attempts to delete User A's fact
    res_del = await client.delete(f"/api/v1/patients/{patient_a}/context/{fact_id}", headers=headers_b)
    assert res_del.status_code == 404

    # User B attempts to read or toggle memory settings
    res_get_pref = await client.get(f"/api/v1/patients/{patient_a}/memory-settings", headers=headers_b)
    assert res_get_pref.status_code == 404

    res_patch_pref = await client.patch(
        f"/api/v1/patients/{patient_a}/memory-settings",
        json={"memory_enabled": False},
        headers=headers_b,
    )
    assert res_patch_pref.status_code == 404


@pytest.mark.asyncio
async def test_context_capture_allergies_and_symptoms(client: AsyncClient):
    """Test capturing explicit allergy statements and severe symptom patterns with exact dates."""
    token, patient_id = await create_user_and_patient(client, "ctx_allergies@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Allergy extraction
    res_allergy = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I am allergic to peanuts since 2019."},
        headers=headers,
    )
    assert res_allergy.status_code == 201
    assert res_allergy.json()["facts"][0]["fact_type"] == "allergy"
    assert res_allergy.json()["facts"][0]["normalized_fact"]["allergen"] == "Peanuts"
    assert res_allergy.json()["facts"][0]["effective_date"] == "2019"

    # Symptom extraction with full date (YYYY-MM-DD)
    res_symptom = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I am experiencing severe chest pain since 2026-04-12."},
        headers=headers,
    )
    assert res_symptom.status_code == 201
    fact = res_symptom.json()["facts"][0]
    assert fact["fact_type"] == "symptom"
    assert "chest pain" in fact["normalized_fact"]["symptom_name"].lower()
    assert fact["normalized_fact"]["severity"] == "severe"
    assert fact["effective_date"] == "2026-04-12"


@pytest.mark.asyncio
async def test_context_capture_non_medical_statement(client: AsyncClient):
    """Test statement with no structured medical facts returns status no_facts_found or historical event."""
    token, patient_id = await create_user_and_patient(client, "ctx_nonmed@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Irrelevant short greeting / statement
    res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "hi"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["status"] == "no_facts_found"
    assert res.json()["facts_captured"] == 0


@pytest.mark.asyncio
async def test_context_filter_needs_confirmation(client: AsyncClient):
    """Test listing context facts filtered by needs_confirmation flag."""
    token, patient_id = await create_user_and_patient(client, "ctx_filter@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1 confident fact
    await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I take Metformin 500 mg daily."},
        headers=headers,
    )
    # 1 uncertain fact
    await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "Maybe I took something yesterday."},
        headers=headers,
    )

    # Filter needs_confirmation=True
    res_true = await client.get(f"/api/v1/patients/{patient_id}/context?needs_confirmation=true", headers=headers)
    assert res_true.status_code == 200
    assert len(res_true.json()) == 1
    assert res_true.json()[0]["needs_confirmation"] is True

    # Filter needs_confirmation=False
    res_false = await client.get(f"/api/v1/patients/{patient_id}/context?needs_confirmation=false", headers=headers)
    assert res_false.status_code == 200
    assert len(res_false.json()) == 1
    assert res_false.json()[0]["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_context_fact_boundary_and_error_handling(client: AsyncClient):
    """Test invalid ObjectIds, non-existent records, empty patches, and operations on deleted facts."""
    token, patient_id = await create_user_and_patient(client, "ctx_errors@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = "507f1f77bcf86cd799439011"
    invalid_id = "not-an-object-id"

    # Confirm invalid & non-existent
    assert (await client.post(f"/api/v1/patients/{patient_id}/context/{invalid_id}/confirm", headers=headers)).status_code == 404
    assert (await client.post(f"/api/v1/patients/{patient_id}/context/{fake_id}/confirm", headers=headers)).status_code == 404

    # Patch invalid & non-existent
    assert (await client.patch(f"/api/v1/patients/{patient_id}/context/{invalid_id}", json={"confidence": 0.5}, headers=headers)).status_code == 404
    assert (await client.patch(f"/api/v1/patients/{patient_id}/context/{fake_id}", json={"confidence": 0.5}, headers=headers)).status_code == 404

    # Delete invalid & non-existent
    assert (await client.delete(f"/api/v1/patients/{patient_id}/context/{invalid_id}", headers=headers)).status_code == 404
    assert (await client.delete(f"/api/v1/patients/{patient_id}/context/{fake_id}", headers=headers)).status_code == 404

    # Create a fact
    cap_res = await client.post(
        f"/api/v1/patients/{patient_id}/context/capture",
        json={"statement": "I take Metformin 500 mg daily."},
        headers=headers,
    )
    fact_id = cap_res.json()["facts"][0]["id"]

    # Empty patch should return existing fact unchanged
    empty_patch = await client.patch(f"/api/v1/patients/{patient_id}/context/{fact_id}", json={}, headers=headers)
    assert empty_patch.status_code == 200
    assert empty_patch.json()["id"] == fact_id

    # Patch with record_status
    status_patch = await client.patch(
        f"/api/v1/patients/{patient_id}/context/{fact_id}",
        json={"record_status": "clinician_verified"},
        headers=headers,
    )
    assert status_patch.status_code == 200
    assert status_patch.json()["record_status"] == "clinician_verified"

    # Delete fact
    del_res = await client.delete(f"/api/v1/patients/{patient_id}/context/{fact_id}", headers=headers)
    assert del_res.status_code == 200

    # Repeat operations on deleted fact must return 404
    assert (await client.post(f"/api/v1/patients/{patient_id}/context/{fact_id}/confirm", headers=headers)).status_code == 404
    assert (await client.patch(f"/api/v1/patients/{patient_id}/context/{fact_id}", json={"confidence": 0.8}, headers=headers)).status_code == 404
    assert (await client.delete(f"/api/v1/patients/{patient_id}/context/{fact_id}", headers=headers)).status_code == 404


def test_context_extractor_empty_string():
    """Verify CandidateFactExtractor returns empty list when given an empty or whitespace string."""
    from app.services.context_extractor import context_extractor
    assert context_extractor.extract_candidate_facts("") == []
    assert context_extractor.extract_candidate_facts("   ") == []


