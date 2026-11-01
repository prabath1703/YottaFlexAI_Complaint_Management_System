import random
from datetime import datetime, timedelta
from faker import Faker


fake = Faker()
Faker.seed(20261022)


def generate_customers(count, rng):
    customers = []

    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 10, 1)

    for i in range(1, count + 1):
        customer_id = f"CUS-{i:06d}"

        customer_since = start_date + timedelta(
            days=rng.randint(
                0,
                (end_date - start_date).days
            )
        )

        customers.append({
            "customer_id": customer_id,
            "name": fake.name(),
            "email": fake.unique.email(),
            "phone": fake.numerify("+91-##########"),
            "customer_since": customer_since.strftime("%Y-%m-%d"),
            "vulnerable_customer_flag": rng.random() < 0.05,
            "created_at": customer_since.strftime("%Y-%m-%d %H:%M:%S")
        })

    return customers


def generate_products(count, rng):

    categories = [
        "Electronics",
        "Home Appliances",
        "Mobile Accessories",
        "Fashion",
        "Grocery",
        "Beauty",
        "Furniture",
        "Sports",
        "Books",
        "Other"
    ]

    risk_levels = [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]

    products = []

    for i in range(1, count + 1):

        product_id = f"PRD-{i:06d}"

        products.append({
            "product_id": product_id,
            "product_name": f"Product {i:04d}",
            "product_category": rng.choice(categories),
            "unit_price": round(
                rng.uniform(100, 50000),
                2
            ),
            "safety_risk_level": rng.choice(risk_levels),
            "active_flag": True
        })

    return products


def generate_categories():

    category_data = [
        ("CAT-01", "DELIVERY", "Delivery and shipping issues"),
        ("CAT-02", "PAYMENT", "Payment related complaints"),
        ("CAT-03", "REFUND", "Refund related complaints"),
        ("CAT-04", "PRODUCT_QUALITY", "Product quality complaints"),
        ("CAT-05", "PRODUCT_SAFETY", "Product safety complaints"),
        ("CAT-06", "CANCELLATION", "Order cancellation complaints"),
        ("CAT-07", "ACCOUNT", "Customer account issues"),
        ("CAT-08", "BILLING", "Billing and invoice issues"),
        ("CAT-09", "SERVICE", "Customer service complaints"),
        ("CAT-10", "OTHER", "Other complaints")
    ]

    categories = []

    for category_id, name, description in category_data:

        categories.append({
            "category_id": category_id,
            "category_name": name,
            "description": description
        })

    return categories