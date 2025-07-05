import os
from typing import Dict, Any
import boto3


log_dir = os.path.join("..", "..", "logs")


class AgentConfig:
    """Configuration for the ReAct Agent"""

    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    BEDROCK_MODEL_ID = "arn:aws:bedrock:us-west-2:397659954198:inference-profile/us.anthropic.claude-opus-4-20250514-v1:0"
    session = boto3.Session(
        aws_access_key_id="ASIAVZFTBLQLEPV7GY4L",
        aws_secret_access_key="Fun+9QnlRAtNCNld/QcV1pUsDKz5F/qctZI4EtMV",
        aws_session_token="IQoJb3JpZ2luX2VjEEMaCXVzLWVhc3QtMSJHMEUCIFsQZaYZA2Iq+rIKtDo0L9N58uw8Pp6OeUx6vmvcl6tVAiEAhtCtaa4pTv7vS1xILt7p/lA+gleE9S91Wiry+94tjjcqmQIITBABGgwzOTc2NTk5NTQxOTgiDPUwOTFfP+wWUVt57yr2AYPGq3IfuznU2A3SKrmEVvA2k7wEHQkn7K6tTeR4J/4JCee5+6KWCWtk9ZtwKnkoaMovk6et9O58eYVUFsKmeO2ouDYkF5XJt/VfMsx7w1+VEXWHbZb7PEKWi/q8i26WNaJ0iMw4F5sZWfSmG/7nSHUFaQ6OjElNpb0FYwMB3Bz48u+JL78uMGy48FQJ7+chLs4ECqCMS1qLfiStfHbfUGFfitM5wYwx6JNQOo+QgOCW2Xbm/111if56RrFqAKR9DEUnu8p8CbIdGwYhiqLUrkZ5QgvUxr4xC69+rlCJc6G0KoDm6L2ahUOWOeUeqOjUVxuvGTTHIDCh3KXDBjqdASDNNeqGQ9k6Dpfc8fCdATk1aQmQ+YWhVhz5rg9m7La27O6FeWl6CrHAEnkC8kz2yuBzPtonjZ8WOhVtwqNAnkZzYB3JOAvBqA86LMkzq+45yrFsN6QAvAoiHw7wlvX+7BdJ3g5dK6QBlwefawwvyA4IDsWfN5VXflbuPsajy9VyII2lNhy9nhzn8H34yq6K9TmYoDZzKiKu1v3jTGo=",
    )

    # Model parameters
    MODEL_KWARGS = {"temperature": 0.1, "max_tokens": 2000, "top_p": 0.9}

    # Agent parameters
    MAX_ITERATIONS = 5
    DEFAULT_LOG_FILE = "./logs/realistic_payment_result_logs_20250705_233514.jsonl"

    # Tool configuration
    TOOL_CONFIG = {
        "log_analyzer": {"timeout": 30, "retry_attempts": 2},
        "failure_analyzer": {"timeout": 20, "retry_attempts": 1},
        "provider_health": {"timeout": 15, "retry_attempts": 1},
    }
