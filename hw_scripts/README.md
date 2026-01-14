# OpenRouter API Key Manager

Python script for managing OpenRouter API keys for students.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenRouter provisioning key as an environment variable:
   ```bash
   export OPENROUTER_PROVISIONING_KEY="your-provisioning-key-here"
   ```

## Usage

### Create keys
```bash
./openrouter_key.py create 10 --prefix student --limit 5.0 --reset monthly
```

Options:
- `n`: Number of keys to create (required)
- `--prefix`: Name prefix (default: "student")
- `--limit`: Spending limit in USD (default: 5.0)
- `--reset`: Limit reset period - "daily", "weekly", "monthly", or "none" (default: "monthly")
- `--expires`: Expiration date in ISO 8601 format (e.g., "2025-06-01T23:59:59Z")
- `--output`: Output CSV file (default: "student_keys.csv")

### List keys
```bash
./openrouter_key.py list --prefix student
```

Options:
- `--prefix`: Filter by name prefix
- `--include-disabled`: Include disabled keys

### Delete keys
```bash
./openrouter_key.py delete --prefix student
# or
./openrouter_key.py delete --from-csv student_keys.csv
```

Options:
- `--prefix`: Delete all keys with this name prefix
- `--from-csv`: Delete keys listed in CSV file (must have 'hash' column)
- `--dry-run`: Show what would be deleted without actually deleting

## Features

- Automatic retry with exponential backoff for rate limiting (429 errors)
- CSV output for created keys
- Prevents duplicate key creation by checking existing CSV
- Paginated listing for large numbers of keys
- Safe deletion with confirmation prompt
