from config_agent import AgentConfig


def setup_agent():
    """Quick setup for the ReAct agent"""
    import boto3
    from botocore.exceptions import ClientError

    try:
        session = boto3.Session(
            aws_access_key_id="ASIAVZFTBLQLEPV7GY4L",
            aws_secret_access_key="Fun+9QnlRAtNCNld/QcV1pUsDKz5F/qctZI4EtMV",
            aws_session_token="IQoJb3JpZ2luX2VjEEMaCXVzLWVhc3QtMSJHMEUCIFsQZaYZA2Iq+rIKtDo0L9N58uw8Pp6OeUx6vmvcl6tVAiEAhtCtaa4pTv7vS1xILt7p/lA+gleE9S91Wiry+94tjjcqmQIITBABGgwzOTc2NTk5NTQxOTgiDPUwOTFfP+wWUVt57yr2AYPGq3IfuznU2A3SKrmEVvA2k7wEHQkn7K6tTeR4J/4JCee5+6KWCWtk9ZtwKnkoaMovk6et9O58eYVUFsKmeO2ouDYkF5XJt/VfMsx7w1+VEXWHbZb7PEKWi/q8i26WNaJ0iMw4F5sZWfSmG/7nSHUFaQ6OjElNpb0FYwMB3Bz48u+JL78uMGy48FQJ7+chLs4ECqCMS1qLfiStfHbfUGFfitM5wYwx6JNQOo+QgOCW2Xbm/111if56RrFqAKR9DEUnu8p8CbIdGwYhiqLUrkZ5QgvUxr4xC69+rlCJc6G0KoDm6L2ahUOWOeUeqOjUVxuvGTTHIDCh3KXDBjqdASDNNeqGQ9k6Dpfc8fCdATk1aQmQ+YWhVhz5rg9m7La27O6FeWl6CrHAEnkC8kz2yuBzPtonjZ8WOhVtwqNAnkZzYB3JOAvBqA86LMkzq+45yrFsN6QAvAoiHw7wlvX+7BdJ3g5dK6QBlwefawwvyA4IDsWfN5VXflbuPsajy9VyII2lNhy9nhzn8H34yq6K9TmYoDZzKiKu1v3jTGo=",
        )
        # Test AWS connection
        bedrock = session.client("bedrock-runtime", region_name=AgentConfig.AWS_REGION)
        print("✓ AWS Bedrock connection successful")

        # Verify model access
        response = bedrock.invoke_model(
            modelId=AgentConfig.BEDROCK_MODEL_ID,
            body='{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}',
        )
        print("✓ Claude model access verified")

        return True
    except ClientError as e:
        print(f"✗ AWS setup error: {e}")
        return False
    except Exception as e:
        print(f"✗ Setup error: {e}")
        return False


if __name__ == "__main__":
    setup_agent()
