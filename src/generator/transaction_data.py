from datetime import datetime, timedelta


def generate_orders(customers, products, count, rng):

    orders = []

    order_statuses = [
        "DELIVERED",
        "SHIPPED",
        "PROCESSING",
        "CANCELLED",
        "REFUNDED"
    ]

    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 10, 20)

    for i in range(1, count + 1):

        customer = rng.choice(customers)
        product = rng.choice(products)

        order_date = start_date + timedelta(
            days=rng.randint(
                0,
                (end_date - start_date).days
            ),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59)
        )

        quantity = rng.randint(1, 5)

        unit_price = product["unit_price"]

        order_total = round(
            quantity * unit_price,
            2
        )

        status = rng.choice(order_statuses)

        orders.append({
            "order_id": f"ORD-2026-{i:06d}",
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "order_date": order_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "quantity": quantity,
            "unit_price": unit_price,
            "order_total": order_total,
            "order_status": status
        })

    return orders


def generate_complaints(
    customers,
    products,
    orders,
    categories,
    count,
    rng
):

    complaints = []

    channels = [
        "EMAIL",
        "PHONE",
        "CHAT",
        "WEB"
    ]

    sentiments = [
        "POSITIVE",
        "NEUTRAL",
        "NEGATIVE",
        "VERY_NEGATIVE"
    ]

    severities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    start_date = datetime(2026, 1, 5)
    end_date = datetime(2026, 10, 25)

    category_map = {
        category["category_name"]: category["category_id"]
        for category in categories
    }

    for i in range(1, count + 1):

        customer = rng.choice(customers)

        customer_orders = [
            order
            for order in orders
            if order["customer_id"] == customer["customer_id"]
        ]

        # Most complaints are associated with an order.
        if customer_orders and rng.random() < 0.90:
            order = rng.choice(customer_orders)
            order_id = order["order_id"]
            product_id = order["product_id"]
        else:
            order_id = None
            product = rng.choice(products)
            product_id = product["product_id"]

        category = rng.choice(categories)

        category_name = category["category_name"]

        sentiment = rng.choice(sentiments)
        severity = rng.choice(severities)

        complaint_time = start_date + timedelta(
            days=rng.randint(
                0,
                (end_date - start_date).days
            ),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59)
        )

        safety_issue = (
            category_name == "PRODUCT_SAFETY"
            or rng.random() < 0.03
        )

        repeat_complaint = rng.random() < 0.12

        complaints.append({
            "complaint_id": f"CMP-2026-{i:06d}",
            "customer_id": customer["customer_id"],
            "order_id": order_id,
            "product_id": product_id,
            "channel": rng.choice(channels),
            "created_at": complaint_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "description": (
                f"Customer reported an issue related to "
                f"{category_name.lower()}."
            ),
            "category_id": category_map[category_name],
            "category": category_name,
            "severity": severity,
            "sentiment": sentiment,
            "repeat_complaint_flag": repeat_complaint,
            "related_complaint_id": None,
            "safety_issue_flag": safety_issue,
            "priority": None,
            "status": "OPEN"
        })

    return complaints