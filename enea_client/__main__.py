import argparse
import logging
import os
import sys

from enea_client.app import App
from enea_client.config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch CSV from enea portal")
    parser.add_argument(
        "--enea-login",
        default=os.getenv("ENEA_CLIENT_LOGIN"),
        help="Enea login username (env: ENEA_CLIENT_LOGIN)",
    )
    parser.add_argument(
        "--enea-password",
        default=os.getenv("ENEA_CLIENT_PASSWORD"),
        help="Enea login password (env: ENEA_CLIENT_PASSWORD)",
    )
    parser.add_argument(
        "--enea-pod-guid",
        default=os.getenv("ENEA_CLIENT_POD_GUID"),
        help="Enea Point of Delivery GUID (env: ENEA_CLIENT_POD_GUID)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("ENEA_CLIENT_OUTPUT_DIR"),
        help="Directory path to save CSV files (env: ENEA_CLIENT_OUTPUT_DIR)",
    )
    parser.add_argument(
        "--dates",
        default=os.getenv("ENEA_CLIENT_DATE"),
        help="Dates in format MM.YYYY, separated by commas (env: ENEA_CLIENT_DATE)",
    )
    parser.add_argument(
        "--post-process-script",
        default=os.getenv("ENEA_CLIENT_POST_PROCESS_SCRIPT"),
        help="Path to post-processing script (env: ENEA_CLIENT_POST_PROCESS_SCRIPT)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Validate required fields
    required_fields = {
        "dates": args.dates,
        "output_dir": args.output_dir,
        "enea_login": args.enea_login,
        "enea_password": args.enea_password,
        "enea_pod_guid": args.enea_pod_guid,
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        parser.error(f"Missing required arguments: {', '.join(missing)}")

    # Create a config object
    config = Config(
        dates=args.dates.split(",") if args.dates else [],
        output_dir=args.output_dir,
        enea_login=args.enea_login,
        enea_password=args.enea_password,
        enea_pod_guid=args.enea_pod_guid,
        post_process_script=args.post_process_script,
    )

    # Set up logging
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    app = App(config)
    app.call()

if __name__ == "__main__":
    main()
