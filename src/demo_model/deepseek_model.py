import json
import ollama
import boto3
from langchain_aws import ChatBedrockConverse
import time
import random
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import ChatPromptTemplate
import re

JSONL_PATH = "./logs/realistic_payment_result_logs_20250705_215551.jsonl"
OUTPUT_PATH = "./logs/deepseek_distilled_dataset.jsonl"
AWS_DEFAULT_REGION="us-west-2"
AWS_ACCESS_KEY_ID="ASIATBCYYTPGVW42XAS3"
AWS_SECRET_ACCESS_KEY="7+/tAOezdam9EN8PkyxwHUlilJRCf9eiJmBlvjga"
AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEEAaCXVzLWVhc3QtMSJGMEQCICmQFl29pueU9Oqxo+meQx0OOjW98vAA33eYpMWkcEaxAiAgrukCnCzTX0u7xtChDtxQ2rj/TK5peHaBBAg4Ic1kdyqZAghIEAAaDDIwODQ5MjA3NTk4MSIMMaL5kWAvO2wQ6tRNKvYBx8ithT3XyvYqnLcSy2p9SX8W8QpgcI5q5PdLRsSiNUdoGJ+Ukzm95oCdHm2Bi0TyYU61EqZTS0UxTk9altu/MyhPoU9RHhFs5YF/kEvQP49Y+FDdGM8FUjgNAfO/jm0c/ybZbOIWqWeE5Wv1Q0A1SeVKPrkI6K1sIzfB3VaoGmkTac4us5GOlNqeiCssVLey7NO6BMwpDHSIhogy1v6M1RF3BGBokLoMtOdhGBUYvK6HXRpfOXOIdaRScUszK2++S5cMZpJWqwDfP3iI42M1zpi9UurEspZawOAidp8wirtQkp4yOtTV2NkGmFJUPwY3WOxjkER3MIv+pMMGOp4BAn9NX8BXekH7hWfHX11qrhoD2b5nJfRMdpm0peYlE+trbrxiYqnl0gNDdUCQ5fs2sBcn5bHznZjYIIIxtpMLstwy4pS1MzBWhI+Y6JbU23i90vSnrfibhQPXfFFkNsXadOLt0TaJrO0duCdz1Qb+QO5NRrbkOQBUEvux3t9ArueTHerxHaUoQr/4aDrLmZfKbA7TNP0zRQUOUVYr0IY="

print(f"📂 Reading from: {JSONL_PATH}")
print(f"💾 Writing to: {OUTPUT_PATH}")
client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
)

llm = ChatBedrockConverse(
    model_id="us.deepseek.r1-v1:0",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_DEFAULT_REGION,
)
def format_deepseek_response(raw_response):
    """
    Convert DeepSeek output (list of dicts) into "<think>...</think>\n{"Success" | "Failure"}" format.
    """
    try:
        if isinstance(raw_response, str):
            # If DeepSeek returned stringified JSON
            parsed = json.loads(raw_response)
        else:
            parsed = raw_response

        # Extract reasoning content
        reasoning = ""
        outcome = ""
        for block in parsed:
            if block.get("type") == "reasoning_content":
                reasoning = block["reasoning_content"].get("text", "").strip()
            if block.get("type") == "text":
                outcome = block["text"].strip().replace('\n', '')

        formatted = f"<think>{reasoning}</think>\n{json.dumps(outcome)}"
        return formatted

    except Exception as e:
        print(f"⚠️ Failed to format DeepSeek response: {e}")
        return f"<think>Could not parse reasoning</think>\n\"Unknown\""
    
def use_bedrock_deepseek(input_prompt):
    messages = [
    (
        "system",
        "You are a payment gateway risk expert. Predict if the transaction will succeed or fail. Keep the answer strictly as 'Success' or 'Failure'",
    ),
        ("human", input_prompt),
    ]

    response = llm.invoke( input=messages)
    return response.content
    



# with open(JSONL_PATH, "r") as f_input, open(OUTPUT_PATH, "w") as f_output:
#     for idx, line in enumerate(f_input, start=1):
#         try:
#             log = json.loads(line)
#             txn = log.get("transaction", {})
#             customer = txn.get("customer_info", {})
#             instrument = txn.get("payment_instrument", {})
#             route = txn.get("route_history", {})
#             decision = route.get("routing_decision", {})
#             metadata = txn.get("metadata", {})

#             # Extract relevant fields
#             log_id = log.get("transaction_id")
#             currency = txn.get("currency", "UNKNOWN")
#             amount = txn.get("amount", "UNKNOWN")
#             method = instrument.get("method", "UNKNOWN")
#             network = instrument.get("network")
#             brand = instrument.get("brand")
#             issuer = instrument.get("issuer")
#             provider = txn.get("provider", "UNKNOWN")
#             region = customer.get("region", "UNKNOWN")
#             country = customer.get("country", "UNKNOWN")
#             risk_level = customer.get("risk_level")
#             prev_fails = customer.get("previous_failures")
#             success_count = customer.get("successful_payments")
#             preferred = customer.get("preferred_providers", [])
#             routing_strategy = decision.get("strategy_used")
#             cb_state = decision.get("decision_factors", {}).get("circuit_breaker_state")
#             provider_health = decision.get("decision_factors", {}).get("provider_health")
#             est_latency = decision.get("decision_factors", {}).get("estimated_latency")
#             fee = metadata.get("processing_fee")

#             # Build prompt with all available context
#             prompt = f"""Currency: {currency}
# Amount: {amount}
# Method: {method}
# Network: {network}
# Brand: {brand}
# Issuer: {issuer}
# Provider: {provider}
# Region: {region}
# Country: {country}
# Customer Risk Level: {risk_level}
# Previous Failures: {prev_fails}
# Successful Payments: {success_count}
# Preferred Providers: {preferred}
# Routing Strategy: {routing_strategy}
# Circuit Breaker State: {cb_state}
# Provider Health: {provider_health}
# Estimated Latency: {est_latency}
# Processing Fee: {fee}
# → Will this transaction succeed?"""

#             print(f"\n🔹 Processing log #{idx}")
#             print(f"📝 Prompt:\n{prompt}")
#             print("🧠 Sending prompt to DeepSeek-R1...")
#             time.sleep(random.randint(5, 15))
#             # Query DeepSeek-R1
#             raw_response = use_bedrock_deepseek(prompt)
#             response = format_deepseek_response(raw_response)

#             print(f"✅ DeepSeek-R1 response: {response}")

#             # Write to distilled dataset
#             entry = {
#                 "log_id": log.get("provider_transaction_id"),
#                 "prompt": prompt,
#                 "response": response
#             }
#             f_output.write(json.dumps(entry) + "\n")

#         except Exception as e:
#             print(f"❌ Error processing log #{idx}: {e}")

# print("\n✅ Done. All entries written to file.")



