"""
Idempotently declares the RabbitMQ topology described in README.md:

  sentinel.raw_events (topic)          -> event_processing.raw   (Member 3 consumes)
  sentinel.processed_events (topic)    -> dashboard.processed    (Member 4 consumes)
                                        -> ai_analytics.processed (Member 6 consumes)
  sentinel.raw_events.dlx (fanout)     -> event_processing.dlq

Run with:  python -m src.topology
"""

import logging

from src.rabbitmq_client import RabbitMQClient, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sentinel.topology")


def declare_topology(client: RabbitMQClient) -> None:
    cfg = client.config
    ch = client.connect()

    ex = cfg["exchanges"]
    q = cfg["queues"]

    # Dead-letter exchange + queue first, so raw queue can reference it
    ch.exchange_declare(exchange=ex["dead_letter"], exchange_type="fanout", durable=True)
    ch.queue_declare(queue=q["dead_letter"], durable=True)
    ch.queue_bind(queue=q["dead_letter"], exchange=ex["dead_letter"])

    # Raw events exchange + queue (consumed by Member 3)
    ch.exchange_declare(exchange=ex["raw_events"], exchange_type="topic", durable=True)
    ch.queue_declare(
        queue=q["raw_processing"],
        durable=True,
        arguments={
            "x-dead-letter-exchange": ex["dead_letter"],
        },
    )
    ch.queue_bind(queue=q["raw_processing"], exchange=ex["raw_events"], routing_key="#")

    # Processed events exchange + downstream queues (Member 4, Member 6)
    ch.exchange_declare(exchange=ex["processed_events"], exchange_type="topic", durable=True)
    ch.queue_declare(queue=q["dashboard"], durable=True)
    ch.queue_bind(queue=q["dashboard"], exchange=ex["processed_events"], routing_key="#")

    ch.queue_declare(queue=q["ai_analytics"], durable=True)
    ch.queue_bind(queue=q["ai_analytics"], exchange=ex["processed_events"], routing_key="#")

    logger.info("Topology declared successfully:")
    logger.info("  Exchanges: %s", list(ex.values()))
    logger.info("  Queues:    %s", list(q.values()))


if __name__ == "__main__":
    client = RabbitMQClient(load_config())
    declare_topology(client)
    client.close()
