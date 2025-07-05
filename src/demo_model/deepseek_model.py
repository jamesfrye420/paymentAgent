import json
import ollama

JSONL_PATH = "./logs/payment_events.jsonl"
OUTPUT_PATH = "./logs/deepseek_distilled_dataset.jsonl"

print(f"📂 Reading from: {JSONL_PATH}")
print(f"💾 Writing to: {OUTPUT_PATH}")

with open(JSONL_PATH, "r") as f_input, open(OUTPUT_PATH, "w") as f_output:
    for idx, line in enumerate(f_input, start=1):
        log = json.loads(line)

        # Extract fields
        log_id = log.get('log_id')
        context = log.get("context", {})
        currency = context.get("transaction_currency", "UNKNOWN")
        amount = context.get("transaction_amount", "UNKNOWN")
        method = context.get("payment_method", "UNKNOWN")
        provider = log.get("provider", "UNKNOWN")
        region = context.get("customer_region", "UNKNOWN")

        print(f"\n🔹 Processing log #{idx}")
        print(f" - Currency: {currency}")
        print(f" - Amount: {amount}")
        print(f" - Method: {method}")
        print(f" - Provider: {provider}")
        print(f" - Region: {region}")

        # Build prompt
        prompt = f"""Currency: {currency}
Amount: {amount}
Method: {method}
Provider: {provider}
Region: {region}
→ Will this transaction succeed?"""

        print("🧠 Sending prompt to DeepSeek-R1...")
        print(f"📝 Prompt:\n{prompt}")

        try:
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

            # Write each entry immediately
            entry = {"log_id": log_id, "prompt": prompt, "response": result}
            f_output.write(json.dumps(entry) + "\n")

        except Exception as e:
            print(f"❌ Error processing log #{idx}: {e}")

print("\n✅ Done. All entries written to file.")
