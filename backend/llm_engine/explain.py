"""
LLM Explanation Engine — Uses Groq (Llama 3) to generate human-readable
investigation reports for flagged fraud rings.
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Using Qwen 3.8 27B available on this Groq key. Fallback default matches .env.
MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")


def build_ring_prompt(ring_data: dict) -> str:
    """Build a structured prompt for the LLM from ring data."""
    
    members_summary = ""
    for m in ring_data.get("members", [])[:10]:  # Limit to 10 for token efficiency
        members_summary += (
            f"  - {m['customer_id']}: refund_rate={m.get('refund_rate', 0):.1%}, "
            f"devices={m.get('num_devices_used', 0)}, "
            f"shared_device_users={m.get('shared_device_users', 0)}, "
            f"txns={m.get('total_transactions', 0)}, "
            f"avg_amount=₹{m.get('avg_transaction_amount', 0):,.0f}\n"
        )

    prompt = f"""You are a senior fraud analyst at a fintech company in India. 
Analyze this flagged fraud ring and write an investigation report.

RING ID: {ring_data['ring_id']}
RING TYPE (predicted): {ring_data.get('ring_type', 'Unknown')}
TOTAL MEMBERS: {ring_data.get('ring_size', len(ring_data.get('members', [])))}
MODEL CONFIDENCE: High (flagged by XGBoost + Graph ML)

RING-LEVEL STATS:
- Shared Devices: {ring_data.get('num_shared_devices', 0)}
- Shared IPs: {ring_data.get('num_shared_ips', 0)}
- Shared Payment Instruments: {ring_data.get('num_shared_payments', 0)}
- Average Refund Rate: {ring_data.get('avg_refund_rate', 0):.1%}
- Total Transaction Amount: ₹{ring_data.get('total_amount', 0):,.0f}

MEMBER DETAILS:
{members_summary}

Write your report with these EXACT sections:
1. **Risk Score** (0-100) with severity level (LOW/MEDIUM/HIGH/CRITICAL)
2. **Summary** (2-3 sentences explaining the ring)
3. **Key Evidence** (3-5 numbered bullet points with specific data)
4. **Ring Type Analysis** (explain which fraud archetype this matches and why)
5. **Recommended Action** (freeze, monitor, or escalate)
6. **Estimated Loss** if not caught (rough calculation)

Be specific. Use the numbers provided. Write like a professional analyst, not a chatbot."""

    return prompt


def explain_ring(ring_data: dict) -> str:
    """Call Groq LLM to generate an investigation report for a flagged ring."""
    prompt = build_ring_prompt(ring_data)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior fraud investigation analyst at a major Indian fintech company. You write concise, data-driven investigation reports. Do NOT include any thinking or reasoning tags in your output."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Low temperature for consistent, factual output
            max_tokens=1024,
        )
        result = response.choices[0].message.content
        # Strip <think>...</think> tags from Qwen models
        import re
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
        return result
    except Exception as e:
        return f"⚠️ LLM Error: {str(e)}\n\nFallback: Ring {ring_data['ring_id']} flagged with {ring_data.get('total_members', '?')} members, avg refund rate {ring_data.get('avg_refund_rate', 0):.1%}."


def explain_customer(customer_data: dict) -> str:
    """Generate a brief explanation for why a single customer was flagged."""
    prompt = f"""You are a fraud analyst. Briefly explain (3-4 sentences) why this customer was flagged.

Customer: {customer_data.get('customer_id')}
Refund Rate: {customer_data.get('refund_rate', 0):.1%}
Devices Used: {customer_data.get('num_devices_used', 0)}
Shared Device Users: {customer_data.get('shared_device_users', 0)}
Shared IP Users: {customer_data.get('shared_ip_users', 0)}
Transaction Count: {customer_data.get('total_transactions', 0)}
Avg Amount: ₹{customer_data.get('avg_transaction_amount', 0):,.0f}
Account Age: {customer_data.get('account_age_days', 0)} days

Be specific and mention the exact numbers that are suspicious."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {str(e)}"


def chat_with_ring(ring_data: dict, message: str, history: list) -> str:
    """Multi-turn chat about a specific ring. Ring data is injected as system context."""

    # Build system context from ring data
    members_summary = ""
    for m in ring_data.get("members", [])[:10]:
        members_summary += (
            f"  - {m['customer_id']}: refund_rate={m.get('refund_rate', 0):.1%}, "
            f"devices={m.get('num_devices_used', 0)}, "
            f"shared_device_users={m.get('shared_device_users', 0)}, "
            f"model_confidence={m.get('model_confidence', 0):.1%}, "
            f"txns={m.get('total_transactions', 0)}, "
            f"avg_amount=Rs.{m.get('avg_transaction_amount', 0):,.0f}\n"
        )

    system_prompt = f"""You are a senior fraud investigation analyst at a major Indian fintech company. 
You are investigating a specific fraud ring. Answer the user's questions using the ring data below.
Be specific, use numbers, and write like a professional analyst. Do NOT include any thinking or reasoning tags.

RING DATA:
- Ring ID: {ring_data['ring_id']}
- Type: {ring_data.get('ring_type', 'Unknown')}
- Members: {ring_data.get('ring_size', '?')}
- Shared Devices: {ring_data.get('num_shared_devices', 0)}
- Shared IPs: {ring_data.get('num_shared_ips', 0)}
- Shared Payments: {ring_data.get('num_shared_payments', 0)}
- Avg Refund Rate: {ring_data.get('avg_refund_rate', 0):.1%}
- Total Amount: Rs.{ring_data.get('total_amount', 0):,.0f}

MEMBERS:
{members_summary}"""

    # Build messages list: system + history + new message
    messages = [{"role": "system", "content": system_prompt}]

    for h in history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        result = response.choices[0].message.content
        import re
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
        return result
    except Exception as e:
        return f"LLM Error: {str(e)}"
