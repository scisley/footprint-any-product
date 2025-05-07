#!/usr/bin/env python3

import sys
import json
import muir_api_client

# This script is a simple wrapper around the muir_api_client.py
# It's used to call the API functions from our Next.js server

if __name__ == "__main__":
    # Check if there are enough arguments
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing command. Usage: python3 muir_api_wrapper.py <command> [args...]"
        }))
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "get_info":
            result = muir_api_client.get_info()
            print(json.dumps(result))

        elif command == "get_procurement_ids":
            page = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            per_page = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            result = muir_api_client.get_procurement_ids(page, per_page)
            print(json.dumps(result))

        elif command == "get_procurement_run":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Procurement ID is required"}))
                sys.exit(1)
            procurement_id = sys.argv[2]
            result = muir_api_client.get_procurement_run(procurement_id)
            print(json.dumps(result))

        elif command == "get_all_runs":
            page = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            per_page = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            result = muir_api_client.get_all_runs(page, per_page)
            print(json.dumps(result))

        elif command == "get_run_by_id":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Run ID is required"}))
                sys.exit(1)
            run_id = sys.argv[2]
            result = muir_api_client.get_run_by_id(run_id)
            print(json.dumps(result))

        elif command == "create_runs":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "JSON file path is required"}))
                sys.exit(1)
            file_path = sys.argv[2]
            with open(file_path, 'r') as file:
                runs_data = json.load(file)
            result = muir_api_client.create_runs(runs_data)
            print(json.dumps(result))

        else:
            print(json.dumps({
                "error": f"Unknown command: {command}"
            }))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "error": str(e)
        }))
        sys.exit(1)