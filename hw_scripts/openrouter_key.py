#!/usr/bin/env python3
import os
import sys
import time
import csv

# Check for required dependencies
try:
    import requests
except ImportError:
    print("Error: Missing required dependency 'requests'", file=sys.stderr)
    print("\nPlease install dependencies by running:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    print("\nOr install requests directly:", file=sys.stderr)
    print("  pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://openrouter.ai/api/v1/keys"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds


class RateLimitExhausted(Exception):
    """Raised when rate limit retries are exhausted."""
    pass


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """
    Make an HTTP request with exponential backoff retry on rate limit (429) errors.

    Args:
        method: HTTP method (get, post, delete)
        url: Request URL
        **kwargs: Arguments passed to requests

    Returns:
        Response object

    Raises:
        RateLimitExhausted: If max retries exceeded due to rate limiting
        requests.exceptions.RequestException: For other request errors
    """
    backoff = INITIAL_BACKOFF

    for attempt in range(MAX_RETRIES):
        response = getattr(requests, method)(url, **kwargs)

        if response.status_code == 429:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⏳ Rate limited, waiting {backoff:.1f}s before retry ({attempt + 1}/{MAX_RETRIES})...")
                time.sleep(backoff)
                backoff *= 2  # exponential backoff
                continue
            else:
                raise RateLimitExhausted(f"Rate limit exceeded after {MAX_RETRIES} retries")

        return response

    # Should not reach here, but just in case
    raise RateLimitExhausted(f"Rate limit exceeded after {MAX_RETRIES} retries")


def get_headers():
    provisioning_key = os.environ.get("OPENROUTER_PROVISIONING_KEY")
    if not provisioning_key:
        raise ValueError("OPENROUTER_PROVISIONING_KEY environment variable not set")
    return {
        "Authorization": f"Bearer {provisioning_key}",
        "Content-Type": "application/json"
    }


def list_keys(prefix: str | None = None, include_disabled: bool = False) -> list[dict]:
    """
    List all API keys, optionally filtered by name prefix.
    
    Args:
        prefix: Only return keys whose names start with this prefix
        include_disabled: Whether to include disabled keys
    
    Returns:
        List of key objects
    """
    headers = get_headers()
    params = {
        "include_disabled": "true" if include_disabled else "false"
    }
    
    all_keys = []
    offset = 0
    
    while True:
        params["offset"] = str(offset)
        response = request_with_retry("get", BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        keys = data.get("data", [])
        
        if not keys:
            break
            
        all_keys.extend(keys)
        offset += len(keys)
        
        # If we got fewer than expected, we've reached the end
        if len(keys) < 100:
            break
    
    # Filter by prefix if specified
    if prefix:
        all_keys = [k for k in all_keys if k.get("name", "").startswith(prefix)]
    
    return all_keys


def create_keys(
    n: int,
    name_prefix: str = "student",
    limit_usd: float = 5.0,
    limit_reset: str | None = "monthly",
    expires_at: str | None = None,
    output_csv: str = "student_keys.csv"
) -> tuple[list[dict], list[dict]]:
    """
    Create n OpenRouter API keys.
    
    Args:
        n: Number of keys to create
        name_prefix: Prefix for key names (will be "{prefix}_001", "{prefix}_002", etc.)
        limit_usd: Spending limit per key in USD
        limit_reset: Reset period - "daily", "weekly", "monthly", or None
        expires_at: Optional expiration date in ISO 8601 format (e.g., "2025-06-01T23:59:59Z")
        output_csv: Path to save the generated keys
    
    Returns:
        Tuple of (created_keys, failed_keys)
    """
    headers = get_headers()

    # Load existing keys from CSV if it exists
    existing_keys = []
    existing_names = set()
    if os.path.exists(output_csv):
        with open(output_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_keys.append(row)
                existing_names.add(row.get("name", ""))
        if existing_names:
            print(f"Found {len(existing_names)} existing keys in {output_csv}")

    created_keys = []
    failed = []
    skipped = 0

    for i in range(1, n + 1):
        name = f"{name_prefix}_{i:03d}"

        if name in existing_names:
            skipped += 1
            continue
        
        payload = {
            "name": name,
            "limit": limit_usd,
        }
        
        if limit_reset:
            payload["limit_reset"] = limit_reset
        
        if expires_at:
            payload["expires_at"] = expires_at
        
        try:
            response = request_with_retry("post", BASE_URL, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            key_info = {
                "name": name,
                "key": data["key"],
                "hash": data["data"]["hash"],
                "limit_usd": limit_usd,
                "limit_reset": limit_reset or "none",
                "created_at": data["data"]["created_at"]
            }
            created_keys.append(key_info)
            print(f"✓ Created key {i}/{n}: {name}")

        except RateLimitExhausted as e:
            print(f"\n✗ {e}. Stopping.")
            failed.append({"name": name, "error": str(e)})
            break

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg = e.response.json()
                except:
                    error_msg = e.response.text
            failed.append({"name": name, "error": error_msg})
            print(f"✗ Failed to create key {i}/{n}: {name} - {error_msg}")
    
    # Save to CSV (merge existing + new)
    all_keys = existing_keys + created_keys
    if all_keys:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "key", "hash", "limit_usd", "limit_reset", "created_at"])
            writer.writeheader()
            writer.writerows(all_keys)

    # Summary
    print()
    if skipped:
        print(f"⏭ Skipped {skipped} existing keys")
    if created_keys:
        print(f"✓ Created {len(created_keys)} new keys")
    if failed:
        print(f"✗ {len(failed)} keys failed to create")
    if all_keys:
        print(f"📄 Saved {len(all_keys)} total keys to {output_csv}")

    return created_keys, failed


def delete_keys(
    prefix: str | None = None,
    from_csv: str | None = None,
    dry_run: bool = False
) -> tuple[list[str], list[dict]]:
    """
    Delete OpenRouter API keys by prefix or from a CSV file.
    
    Args:
        prefix: Delete all keys whose names start with this prefix
        from_csv: Path to CSV file containing keys to delete (must have 'hash' column)
        dry_run: If True, only show what would be deleted without actually deleting
    
    Returns:
        Tuple of (deleted_names, failed_deletions)
    """
    headers = get_headers()
    
    keys_to_delete = []
    
    if from_csv:
        # Load keys from CSV
        with open(from_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "hash" in row:
                    keys_to_delete.append({"name": row.get("name", "unknown"), "hash": row["hash"]})
                else:
                    print(f"⚠ CSV row missing 'hash' column: {row}")
    elif prefix:
        # Fetch keys matching prefix
        print(f"Fetching keys with prefix '{prefix}'...")
        keys = list_keys(prefix=prefix, include_disabled=True)
        keys_to_delete = [{"name": k["name"], "hash": k["hash"]} for k in keys]
    else:
        raise ValueError("Must specify either 'prefix' or 'from_csv'")
    
    if not keys_to_delete:
        print("No keys found to delete.")
        return [], []
    
    print(f"\nFound {len(keys_to_delete)} keys to delete:")
    for k in keys_to_delete:
        print(f"  - {k['name']}")
    
    if dry_run:
        print("\n[DRY RUN] No keys were actually deleted.")
        return [k["name"] for k in keys_to_delete], []
    
    # Confirm deletion
    confirm = input(f"\nAre you sure you want to delete {len(keys_to_delete)} keys? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return [], []
    
    deleted = []
    failed = []
    
    for i, key in enumerate(keys_to_delete, 1):
        try:
            response = request_with_retry("delete", f"{BASE_URL}/{key['hash']}", headers=headers)
            response.raise_for_status()
            deleted.append(key["name"])
            print(f"✓ Deleted {i}/{len(keys_to_delete)}: {key['name']}")

        except RateLimitExhausted as e:
            print(f"\n✗ {e}. Stopping.")
            failed.append({"name": key["name"], "error": str(e)})
            break

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg = e.response.json()
                except:
                    error_msg = e.response.text
            failed.append({"name": key["name"], "error": error_msg})
            print(f"✗ Failed to delete {i}/{len(keys_to_delete)}: {key['name']} - {error_msg}")
    
    print(f"\n✓ Deleted {len(deleted)} keys")
    if failed:
        print(f"✗ {len(failed)} keys failed to delete")
    
    return deleted, failed


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage OpenRouter API keys for students",
        epilog='Environment: Set "OPENROUTER_PROVISIONING_KEY" to your provisioning API key.'
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new API keys")
    create_parser.add_argument("n", type=int, help="Number of keys to create")
    create_parser.add_argument("--prefix", default="student", help="Name prefix (default: student)")
    create_parser.add_argument("--limit", type=float, default=5.0, help="Spending limit in USD (default: 5.0)")
    create_parser.add_argument("--reset", choices=["daily", "weekly", "monthly", "none"], default="monthly",
                               help="Limit reset period (default: monthly)")
    create_parser.add_argument("--expires", help="Expiration date in ISO 8601 format (e.g., 2025-06-01T23:59:59Z)")
    create_parser.add_argument("--output", default="student_keys.csv", help="Output CSV file (default: student_keys.csv)")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete API keys")
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument("--prefix", help="Delete all keys with this name prefix")
    delete_group.add_argument("--from-csv", help="Delete keys listed in this CSV file (must have 'hash' column)")
    delete_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument("--prefix", help="Filter by name prefix")
    list_parser.add_argument("--include-disabled", action="store_true", help="Include disabled keys")
    
    args = parser.parse_args()

    try:
        if args.command == "create":
            reset = None if args.reset == "none" else args.reset
            create_keys(
                n=args.n,
                name_prefix=args.prefix,
                limit_usd=args.limit,
                limit_reset=reset,
                expires_at=args.expires,
                output_csv=args.output
            )

        elif args.command == "delete":
            delete_keys(
                prefix=args.prefix,
                from_csv=args.from_csv,
                dry_run=args.dry_run
            )

        elif args.command == "list":
            keys = list_keys(prefix=args.prefix, include_disabled=args.include_disabled)
            if keys:
                print(f"Found {len(keys)} keys:\n")
                for k in keys:
                    status = "disabled" if k.get("disabled") else "active"
                    limit = k.get("limit", "unlimited")
                    usage = k.get("usage", 0)
                    print(f"  {k['name']}: ${usage:.2f} / ${limit} ({status})")
            else:
                print("No keys found.")

        else:
            parser.print_help()

    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        if "OPENROUTER_PROVISIONING_KEY" in str(e):
            print("\nPlease set the environment variable:", file=sys.stderr)
            print("  export OPENROUTER_PROVISIONING_KEY='your-provisioning-key-here'", file=sys.stderr)
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nAborted by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        print("\nFor more details, run with Python in debug mode:", file=sys.stderr)
        print("  python -u openrouter_key.py ...", file=sys.stderr)
        sys.exit(1)
