import json
import ollama

JSONL_PATH = "./logs/realistic_payment_result_logs_20250705_190524.jsonl"
OUTPUT_PATH = "./logs/deepseek_distilled_dataset.jsonl"

print(f"📂 Reading from: {JSONL_PATH}")
print(f"💾 Writing to: {OUTPUT_PATH}")

with open(JSONL_PATH, "r") as f_input, open(OUTPUT_PATH, "w") as f_output:
    for idx, line in enumerate(f_input, start=1):
        try:
            log = json.loads(line)
            txn = log.get("transaction", {})
            customer = txn.get("customer_info", {})
            instrument = txn.get("payment_instrument", {})
            route = txn.get("route_history", {})
            decision = route.get("routing_decision", {})
            metadata = txn.get("metadata", {})

            # Extract relevant fields
            log_id = log.get("transaction_id")
            currency = txn.get("currency", "UNKNOWN")
            amount = txn.get("amount", "UNKNOWN")
            method = instrument.get("method", "UNKNOWN")
            network = instrument.get("network")
            brand = instrument.get("brand")
            issuer = instrument.get("issuer")
            provider = txn.get("provider", "UNKNOWN")
            region = customer.get("region", "UNKNOWN")
            country = customer.get("country", "UNKNOWN")
            risk_level = customer.get("risk_level")
            prev_fails = customer.get("previous_failures")
            success_count = customer.get("successful_payments")
            preferred = customer.get("preferred_providers", [])
            routing_strategy = decision.get("strategy_used")
            cb_state = decision.get("decision_factors", {}).get("circuit_breaker_state")
            provider_health = decision.get("decision_factors", {}).get("provider_health")
            est_latency = decision.get("decision_factors", {}).get("estimated_latency")
            fee = metadata.get("processing_fee")

            # Build prompt with all available context
            prompt = f"""Currency: {currency}
Amount: {amount}
Method: {method}
Network: {network}
Brand: {brand}
Issuer: {issuer}
Provider: {provider}
Region: {region}
Country: {country}
Customer Risk Level: {risk_level}
Previous Failures: {prev_fails}
Successful Payments: {success_count}
Preferred Providers: {preferred}
Routing Strategy: {routing_strategy}
Circuit Breaker State: {cb_state}
Provider Health: {provider_health}
Estimated Latency: {est_latency}
Processing Fee: {fee}
→ Will this transaction succeed?"""

            print(f"\n🔹 Processing log #{idx}")
            print(f"📝 Prompt:\n{prompt}")
            print("🧠 Sending prompt to DeepSeek-R1...")

            # Query DeepSeek-R1
            response = ollama.chat(
                model="deepseek-r1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a payment gateway risk expert. Predict if the transaction will succeed or fail, and keep the answer as just 'Success' or 'Failure'."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            result = response["message"]["content"].strip()
            print(f"✅ DeepSeek-R1 response: {result}")

            # Write to distilled dataset
            entry = {
                "log_id": log.get("provider_transaction_id"),
                "prompt": prompt,
                "response": result
            }
            f_output.write(json.dumps(entry) + "\n")

        except Exception as e:
            print(f"❌ Error processing log #{idx}: {e}")

print("\n✅ Done. All entries written to file.")
