import requests
import os
import json
import uuid # Import uuid for type hinting/clarity

# --- Configuration ---
# Replace with the actual base URL provided by Muir.ai
# Example: BASE_URL = "https://api.muir.ai"
BASE_URL = "YOUR_MUIR_API_BASE_URL"

# Your API Key should be stored in an environment variable for security.
# Set the environment variable MUIR_API_KEY before running this script.
API_KEY = os.environ.get("MUIR_API_KEY")

if not API_KEY:
    print("Error: MUIR_API_KEY environment variable not set.")
    print("Please set it using: export MUIR_API_KEY='YOUR_ACTUAL_API_KEY'")
    exit(1)

# --- Helper Function ---
def _make_request(method, endpoint, params=None, json_data=None):
    """Helper function to make API requests."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "APIKey": API_KEY,
        "Accept": "*/*",
    }
    if json_data is not None:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_data
        )
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Status Code: {e.response.status_code}")
             try:
                 print(f"Response Body: {e.response.json()}")
             except json.JSONDecodeError:
                 print(f"Response Body (text): {e.response.text}")
        return None

# --- API Endpoints ---

def get_info():
    """Retrieves useful information specific to your organization."""
    print("\n--- Getting Organization Info ---")
    endpoint = "/carbon_origin/info"
    data = _make_request("GET", endpoint)
    if data:
        print("Organization Info:")
        print(json.dumps(data, indent=2))
    return data

def get_procurement_ids(page: int = 0, per_page: int = 30):
    """
    Retrieves a paginated list of procurement IDs.

    Args:
        page: Page number (starting from 0).
        per_page: Number of items per page (default 30, max 100).
    """
    print(f"\n--- Getting Procurement IDs (Page {page}, Per Page {per_page}) ---")
    endpoint = "/carbon_origin/procurements/ids"
    params = {"page": page, "per_page": per_page}
    data = _make_request("GET", endpoint, params=params)
    if data:
        print("Procurement IDs:")
        print(json.dumps(data, indent=2))
    return data

def get_procurement_run(procurement_id: str):
    """
    Retrieves the carbon run for a specific procurement.

    Args:
        procurement_id: The UUID of the procurement.
    """
    print(f"\n--- Getting Carbon Run for Procurement ID: {procurement_id} ---")
    endpoint = f"/carbon_origin/procurements/{procurement_id}"
    data = _make_request("GET", endpoint)
    if data:
        print(f"Carbon Run Details for Procurement {procurement_id}:")
        print(json.dumps(data, indent=2))
    return data

def get_all_runs(page: int = 0, per_page: int = 30):
    """
    Retrieves a paginated list of all carbon origin runs submitted by your organization.

    Args:
        page: Page number (starting from 0).
        per_page: Number of items per page (default 30, max 1000).
    """
    print(f"\n--- Getting All Carbon Runs (Page {page}, Per Page {per_page}) ---")
    endpoint = "/carbon_origin/runs"
    params = {"page": page, "per_page": per_page}
    data = _make_request("GET", endpoint, params=params)
    if data:
        print("All Carbon Runs:")
        # Print only the first few runs for brevity if the list is long
        if isinstance(data, list) and len(data) > 5:
            print(json.dumps(data[:5], indent=2))
            print(f"... and {len(data) - 5} more runs.")
        else:
             print(json.dumps(data, indent=2))
    return data


def create_runs(runs_data: list):
    """
    Uploads a list of runs to be analyzed by Carbon Origin.

    Args:
        runs_data: A list of run objects to submit.
                   Each object should match the expected input schema.
    """
    print(f"\n--- Creating {len(runs_data)} Carbon Run(s) ---")
    endpoint = "/carbon_origin/runs"
    data = _make_request("POST", endpoint, json_data=runs_data)
    if data:
        print("Create Runs Response:")
        print(json.dumps(data, indent=2))
    return data

def get_run_by_id(run_id: str):
    """
    Retrieves a single run by its run ID.

    Args:
        run_id: The UUID of the run.
    """
    print(f"\n--- Getting Carbon Run by ID: {run_id} ---")
    endpoint = f"/carbon_origin/runs/{run_id}"
    data = _make_request("GET", endpoint)
    if data:
        print(f"Carbon Run Details for Run ID {run_id}:")
        print(json.dumps(data, indent=2))
    return data


# --- Example Usage ---
if __name__ == "__main__":
    # --- IMPORTANT ---
    # 1. Replace "YOUR_MUIR_API_BASE_URL" above with the actual base URL.
    # 2. Set the environment variable MUIR_API_KEY with your actual API key.
    #    Example: export MUIR_API_KEY='sk-...'

    # Example: Get organization info
    get_info()

    # Example: Get the first page of procurement IDs
    procurement_ids_response = get_procurement_ids(page=0, per_page=10)
    if procurement_ids_response and procurement_ids_response.get("items"):
        first_procurement_id = procurement_ids_response["items"][0]
        # Example: Get the carbon run for the first procurement ID
        get_procurement_run(first_procurement_id)

    # Example: Get the first page of all runs
    all_runs_response = get_all_runs(page=0, per_page=10)
    if all_runs_response and isinstance(all_runs_response, list) and len(all_runs_response) > 0:
         first_run_id_from_list = all_runs_response[0].get("run_id")
         if first_run_id_from_list:
             # Example: Get the first run from the list by its ID
             get_run_by_id(first_run_id_from_list)


    # Example: Create a new run
    # Replace with actual data for a product you want to analyze
    new_runs_data = [
        {
            "product_name": "Sample Product A",
            "product_description": "A test product for API submission.",
            "mass_kg": 2.5,
            "source_location": "Germany",
            "destination_location": "France",
            "upstream_sourcing_countries": ["China", "India"],
            "material_breakdown": {
              "product": "Sample Product A",
              "productMass": 2.5,
              "massUnit": "kg",
              "components": [
                {
                  "component": "Steel",
                  "mass": 2.0,
                  "recycledContent": 0.3
                },
                {
                  "component": "Plastic Packaging",
                  "mass": 0.5,
                  "recycledContent": 0.05
                }
              ]
            },
            "supplier_scope_1_and_2_ef": 0.15 # Example value
        }
        # You can add more run objects to this list
    ]
    # create_runs(new_runs_data) # Uncomment to actually create a run

    # Note: After creating a run, it will be in "PROCESSING" status.
    # You would need to wait and then call get_run_by_id with the returned run_id
    # to get the final "COMPLETED" result.
