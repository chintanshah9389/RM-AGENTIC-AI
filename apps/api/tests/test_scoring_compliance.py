from app.services.compliance import evaluate_compliance
from app.services.scoring import compute_customer_value, compute_propensity
from app.llm.mock_provider import MockLLMProvider


def test_value_score_range():
    result = compute_customer_value(
        {
            "averageMonthlyBalance": 150000,
            "salaryCreditCount": 4,
            "tenureYears": 5,
            "existingProducts": ["SAVINGS", "SALARY", "CREDIT_CARD"],
            "transactionCount": 12,
            "digitalEngagementScore": 80,
        }
    )
    assert 0 <= result["overallScore"] <= 100
    assert result["classification"] in {"LOW", "MEDIUM", "HIGH"}


def test_propensity_disclaimer_fields():
    result = compute_propensity(
        {
            "salaryCreditCount": 3,
            "relevantPurchaseCount": 5,
            "existingProducts": ["CREDIT_CARD"],
            "campaignResponseHistory": [{"response": "INTERESTED"}],
            "digitalEngagementScore": 70,
            "tenureYears": 4,
            "dataQuality": "COMPLETE",
        }
    )
    assert "Demonstration heuristic" in result["explanation"]


def test_do_not_contact_blocks():
    result = evaluate_compliance(
        {
            "marketingConsent": True,
            "whatsappConsent": True,
            "doNotContact": True,
            "contactsThisMonth": 0,
            "maximumContactsPerMonth": 3,
        }
    )
    assert result["contactAllowed"] is False
    assert "DO_NOT_CONTACT" in result["failedChecks"]


def test_whatsapp_consent_required():
    result = evaluate_compliance(
        {
            "marketingConsent": True,
            "whatsappConsent": False,
            "doNotContact": False,
            "contactsThisMonth": 0,
            "maximumContactsPerMonth": 3,
        },
        channel="WHATSAPP",
    )
    assert result["contactAllowed"] is False
    assert "WHATSAPP_CONSENT" in result["failedChecks"]


def test_mock_intent_parser():
    llm = MockLLMProvider()
    parsed = llm.parse_intent(
        "Find high-value customers likely to convert for a Personal Loan this month "
        "and prepare personalized WhatsApp messages."
    )
    assert parsed["productCategory"] == "PERSONAL_LOAN"
    assert parsed["channel"] == "WHATSAPP"
    assert parsed["requiresMessageGeneration"] is True
