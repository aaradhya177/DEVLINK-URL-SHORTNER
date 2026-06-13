import logging


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logging.getLogger("devlink.analytics_worker").info("worker started")


if __name__ == "__main__":
    main()
