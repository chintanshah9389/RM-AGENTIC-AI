from app.core.config import get_settings
from app.llm.factory import get_llm_provider

settings = get_settings()
print("provider_setting=", settings.llm_provider)
print("key_configured=", bool(settings.nvidia_api_key))
print("model=", settings.nvidia_model)

llm = get_llm_provider()
print("provider_class=", llm.__class__.__name__)

intent = llm.parse_intent(
    "Find high-value customers likely to convert for a Personal Loan this month "
    "and prepare personalized WhatsApp messages."
)
print("intent_provider=", intent.get("provider"))
print("product=", intent.get("productCategory"))
print("channel=", intent.get("channel"))
print("nvidiaError=", intent.get("nvidiaError"))

msg = llm.generate_message(
    {
        "firstName": "Priya",
        "productName": "Personal Loan Premium",
        "city": "Mumbai",
        "segment": "PREMIUM",
    }
)
print("message_sample=", msg[:180].replace("\n", " "))
print("NVIDIA_OK")
