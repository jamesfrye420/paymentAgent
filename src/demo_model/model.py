from river import compose
from river import preprocessing
from river import tree
from enum import IntEnum
import pickle
import os

TRAIN_CALL_COUNT = 0
SAVE_INTERVAL = 100  # Save model every 100 learn_one() calls
MODEL_SAVE_PATH = "model_checkpoint.pkl"

def load_model(path=MODEL_SAVE_PATH):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                print(f"[Model Loaded] Restoring from: {path}")
                return pickle.load(f)
        except Exception as e:
            print(f"[Error Loading Model] {e}")
    return None 

# Initialize model and metric
default_model = compose.Pipeline(
    preprocessing.StandardScaler(),
    tree.HoeffdingTreeClassifier()
)
model = load_model() or default_model

"""
Hello @Avik @Arijit
Please test this model with HoeffdingTreeClassifier, AdaptiveRandomForestClassifier, LogisticRegression, GaussianNB, and KNNClassifier
I have added the numeric_encoding function according to the features I saw best fit the use case. Modify it according to your judgement.
You can use river pipelines to combine different models to break the tasks into multiple steps if you want to use advanced models.
Refer to docs: https://riverml.xyz/latest/

"""


def numeric_encoding(features: dict):
    """
        Numeric encoding of features
        "features": {
            "payment_method": "card" | "digital_wallet" | "bank_transfer" | "cryptocurrency" | "buy_now_pay_later",
            "currency": "USD" | "EUR" | "GBP" | "SGD" | "MYR" | "THB" | "IDR" | "VND" | "PHP",
            "transaction_type": "payment" | "refund" | "authorization" | "capture" | "void",
            "region": "north_america" | "europe" | "asia_pacific" | "southeast_asia" | "latin_america" | "middle_east" | "africa",
            "confidence_score": 0.0 - 1.0,
            "network_latency": 0.0 - 1000.0,
            "provider": "stripe" | "paypal" | "razorpay" | "square" | "adyen" | "braintree" | "checkout",
            "is_healthy": false | true,
            "current_load": 0 - 100,
            "regional_success_rate": 0.0 - 1.0
        }
    """
    encoded_features = {}
    
    if features["payment_method"]:
        encoded_features["payment_method"] = PAYMENT_METHOD_MAP.get(
            features["payment_method"], PaymentMethod.CARD
        )
    if features["currency"]:
        encoded_features["currency"] = CURRENCY_MAP.get(
            features["currency"], Currency.USD
        )
    if features["transaction_type"]:
        encoded_features["transaction_type"] = TRANSACTION_TYPE_MAP.get(
            features["transaction_type"], TransactionType.PAYMENT
        )
    if features["region"]:
        encoded_features["region"] = REGION_MAP.get(
            features["region"], Region.NORTH_AMERICA
        )
    if features["confidence_score"]:
        encoded_features["confidence_score"] = int(features["confidence_score"]*100)
    if features["network_latency"]:
        encoded_features["network_latency"] = int(features["network_latency"]*1000)
    if features["provider"]:
        encoded_features["provider"] = PROVIDER_MAP.get(
            features["provider"], Provider.STRIPE
        )
    if features["is_healthy"]:
        encoded_features["is_healthy"] = 1 if features["is_healthy"] else 0
    if features["current_load"]:
        encoded_features["current_load"] = int(features["current_load"])
    if features["regional_success_rate"]:
        encoded_features["regional_success_rate"] = int(features["regional_success_rate"]*100)
    
    return encoded_features

# Real-time handler
def handle_success_prediction(features: dict):
    """
        Predict success or failure of transaction
    """
    global model
    features = numeric_encoding(features)
    # Predict class
    prediction = model.predict_one(features)
    # 0 = fail, 1 = success
    return prediction 

def handle_history(features: dict, true_label: int): 
    """
       
        @param {
            features: {
                "payment_provider": stripe,
                "region": north_america,
                "latency": 200,
            },
            true_label encoding: success(1), fail(0)
        }
    """
    global model, metric
    features = numeric_encoding(features)
    # Predict class

    # If true label is known, update the model and metrics
    model = model.learn_one(features, true_label)

    if TRAIN_CALL_COUNT % SAVE_INTERVAL == 0:
        save_model(model)


def save_model(model, path=MODEL_SAVE_PATH):
    try:
        with open(path, "wb") as f:
            pickle.dump(model, f)
        print(f"[Model Saved] Training checkpoint written to: {path}")
    except Exception as e:
        print(f"[Error Saving Model] {e}")

 # fallback to initial model




class PaymentMethod(IntEnum):
    CARD = 0
    DIGITAL_WALLET = 1
    BANK_TRANSFER = 2
    CRYPTOCURRENCY = 3
    BUY_NOW_PAY_LATER = 4

# Method 1: Using a mapping dictionary (recommended)
PAYMENT_METHOD_MAP = {
    "card": PaymentMethod.CARD,
    "digital_wallet": PaymentMethod.DIGITAL_WALLET,
    "bank_transfer": PaymentMethod.BANK_TRANSFER,
    "cryptocurrency": PaymentMethod.CRYPTOCURRENCY,
    "buy_now_pay_later": PaymentMethod.BUY_NOW_PAY_LATER,
}

class Currency(IntEnum):
    USD = 0
    EUR = 1
    GBP = 2
    SGD = 3
    MYR = 4
    THB = 5
    IDR = 6
    VND = 7
    PHP = 8

CURRENCY_MAP = {
    "USD": Currency.USD,
    "EUR": Currency.EUR,
    "GBP": Currency.GBP,
    "SGD": Currency.SGD,
    "MYR": Currency.MYR,
    "THB": Currency.THB,
    "IDR": Currency.IDR,
    "VND": Currency.VND,
    "PHP": Currency.PHP,
}

class TransactionType(IntEnum):
    PAYMENT = 0
    REFUND = 1
    AUTHORIZATION = 2
    CAPTURE = 3
    VOID = 4

TRANSACTION_TYPE_MAP = {
    "payment": TransactionType.PAYMENT,
    "refund": TransactionType.REFUND,
    "authorization": TransactionType.AUTHORIZATION,
    "capture": TransactionType.CAPTURE,
    "void": TransactionType.VOID,
}

class Region(IntEnum):
    NORTH_AMERICA = 0
    EUROPE = 1
    ASIA_PACIFIC = 2
    SOUTHEAST_ASIA = 3
    LATIN_AMERICA = 4
    MIDDLE_EAST = 5
    AFRICA = 6

REGION_MAP = {
    "north_america": Region.NORTH_AMERICA,
    "europe": Region.EUROPE,
    "asia_pacific": Region.ASIA_PACIFIC,
    "southeast_asia": Region.SOUTHEAST_ASIA,
    "latin_america": Region.LATIN_AMERICA,
    "middle_east": Region.MIDDLE_EAST,
    "africa": Region.AFRICA,
}

class Provider(IntEnum):
    STRIPE = 0
    PAYPAL = 1
    RAZORPAY = 2
    SQUARE = 3
    ADYEN = 4
    BRAINTREE = 5
    CHECKOUT = 6

PROVIDER_MAP = {
    "stripe": Provider.STRIPE,
    "paypal": Provider.PAYPAL,
    "razorpay": Provider.RAZORPAY,
    "square": Provider.SQUARE,
    "adyen": Provider.ADYEN,
    "braintree": Provider.BRAINTREE,
    "checkout": Provider.CHECKOUT,
}