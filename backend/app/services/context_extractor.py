"""Candidate medical fact extractor from natural language statements.

Extracts structured facts (medications, symptoms, conditions, allergies, labs)
from user statements, determines date references, evaluates ambiguity,
and enforces patient attribution rules.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.schemas.medical_record import FactType


class CandidateFactExtractor:
    """Rule-based clinical fact extraction engine for persistent medical memory."""

    # Regex patterns for common clinical categories
    MEDICATION_PATTERNS = [
        r"(?:take|taking|started|prescribed|on)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s*(\d+\s*(?:mg|mcg|g|ml))?",
        r"([a-zA-Z]+)\s+(\d+\s*(?:mg|mcg|g|ml))\s*(?:daily|once|twice|thrice)?",
    ]

    SYMPTOM_PATTERNS = [
        r"(?:experiencing|having|suffer from|complaining of|feel|feeling)\s+(mild|moderate|severe)?\s*([a-zA-Z\s]+?)(?:\s+since|\s+for|\.|$)",
        r"(mild|moderate|severe)\s+([a-zA-Z\s]+?)(?:\s+pain|\s+ache|\s+fever|\s+cough|\.|$)",
    ]

    CONDITION_PATTERNS = [
        r"(?:diagnosed with|have|history of|suffer from)\s+([a-zA-Z0-9\s]+?)(?:\s+in|\s+since|\.|$)",
    ]

    ALLERGY_PATTERNS = [
        r"allergic to\s+([a-zA-Z\s]+?)(?:\s+since|\s+for|\.|$|\s+\d)",
        r"allergy to\s+([a-zA-Z\s]+?)(?:\s+since|\s+for|\.|$|\s+\d)",
        r"allergic to\s+([a-zA-Z]+)",
        r"allergy to\s+([a-zA-Z]+)",
    ]

    # Third-party / family reference indicators (Section 20 safety rule)
    FAMILY_INDICATORS = [
        r"\b(?:my father|my mother|my brother|my sister|my wife|my husband|my son|my daughter|my dad|my mom|my friend|my cousin)\b",
    ]

    # Uncertainty markers
    UNCERTAINTY_INDICATORS = [
        r"\b(?:maybe|perhaps|probably|not sure|i think|unclear|possibly|might have)\b",
    ]

    # Date extraction (YYYY or YYYY-MM-DD)
    YEAR_PATTERN = r"\b(19\d{2}|20\d{2})\b"
    FULL_DATE_PATTERN = r"\b(\d{4}-\d{2}-\d{2})\b"

    def extract_candidate_facts(self, statement: str) -> List[Dict[str, Any]]:
        """Parses a natural-language statement and returns extracted candidate facts."""
        statement_clean = statement.strip()
        if not statement_clean:
            return []

        # Check for third-party subject ambiguity
        is_family_member = any(
            re.search(pat, statement_clean, re.IGNORECASE) for pat in self.FAMILY_INDICATORS
        )
        is_uncertain = any(
            re.search(pat, statement_clean, re.IGNORECASE) for pat in self.UNCERTAINTY_INDICATORS
        )

        effective_date = self._extract_date(statement_clean)
        facts = []

        # 1. Allergies
        for pat in self.ALLERGY_PATTERNS:
            match = re.search(pat, statement_clean, re.IGNORECASE)
            if match:
                allergen = match.group(1).strip()
                facts.append(self._build_fact(
                    fact_type=FactType.ALLERGY,
                    raw_text=statement_clean,
                    normalized={"allergen": allergen.title()},
                    effective_date=effective_date,
                    is_family=is_family_member,
                    is_uncertain=is_uncertain,
                ))
                break

        # 2. Medications
        if not facts:
            for pat in self.MEDICATION_PATTERNS:
                match = re.search(pat, statement_clean, re.IGNORECASE)
                if match:
                    med_name = match.group(1).strip()
                    dose = match.group(2).strip() if len(match.groups()) >= 2 and match.group(2) else None
                    frequency = "daily" if "daily" in statement_clean.lower() else None
                    facts.append(self._build_fact(
                        fact_type=FactType.MEDICATION,
                        raw_text=statement_clean,
                        normalized={
                            "medication_name": med_name.title(),
                            "dosage": dose,
                            "frequency": frequency,
                        },
                        effective_date=effective_date,
                        is_family=is_family_member,
                        is_uncertain=is_uncertain,
                    ))
                    break

        # 3. Conditions
        if not facts:
            for pat in self.CONDITION_PATTERNS:
                match = re.search(pat, statement_clean, re.IGNORECASE)
                if match:
                    condition = match.group(1).strip()
                    facts.append(self._build_fact(
                        fact_type=FactType.CONDITION,
                        raw_text=statement_clean,
                        normalized={"condition_name": condition.title()},
                        effective_date=effective_date,
                        is_family=is_family_member,
                        is_uncertain=is_uncertain,
                    ))
                    break

        # 4. Symptoms
        if not facts:
            for pat in self.SYMPTOM_PATTERNS:
                match = re.search(pat, statement_clean, re.IGNORECASE)
                if match:
                    groups = [g for g in match.groups() if g]
                    symptom = " ".join(groups).strip()
                    severity = "moderate"
                    for s in ["mild", "severe", "moderate"]:
                        if s in statement_clean.lower():
                            severity = s
                            break
                    facts.append(self._build_fact(
                        fact_type=FactType.SYMPTOM,
                        raw_text=statement_clean,
                        normalized={"symptom_name": symptom.title(), "severity": severity},
                        effective_date=effective_date,
                        is_family=is_family_member,
                        is_uncertain=is_uncertain,
                    ))
                    break

        # Fallback if no specific pattern matched but user shared a general statement
        if not facts and len(statement_clean) > 5:
            facts.append(self._build_fact(
                fact_type=FactType.HISTORICAL_EVENT,
                raw_text=statement_clean,
                normalized={"summary": statement_clean[:200]},
                effective_date=effective_date,
                is_family=is_family_member,
                is_uncertain=True,  # General statements always require confirmation
            ))

        return facts

    def _extract_date(self, text: str) -> Optional[str]:
        """Extracts YYYY-MM-DD or YYYY from text."""
        full_match = re.search(self.FULL_DATE_PATTERN, text)
        if full_match:
            return full_match.group(1)
        year_match = re.search(self.YEAR_PATTERN, text)
        if year_match:
            return year_match.group(1)
        return None

    def _build_fact(
        self,
        fact_type: FactType,
        raw_text: str,
        normalized: Dict[str, Any],
        effective_date: Optional[str],
        is_family: bool,
        is_uncertain: bool,
    ) -> Dict[str, Any]:
        """Builds a structured fact payload with confidence and confirmation flags."""
        confidence = 0.95
        needs_confirmation = False

        if is_uncertain:
            confidence = 0.60
            needs_confirmation = True

        if is_family:
            confidence = 0.40
            needs_confirmation = True
            normalized["subject_warning"] = "Statement appears to refer to a family member, not patient."

        return {
            "fact_type": fact_type,
            "original_statement_excerpt": raw_text[:500],
            "normalized_fact": normalized,
            "effective_date": effective_date,
            "confidence": confidence,
            "needs_confirmation": needs_confirmation,
        }


# Singleton extractor instance
context_extractor = CandidateFactExtractor()
