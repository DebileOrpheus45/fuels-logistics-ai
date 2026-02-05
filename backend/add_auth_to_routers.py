"""
Script to add authentication to all API routers.

This script adds `current_user: User = Depends(get_current_user)` to all endpoint functions
and imports the necessary auth dependencies.
"""

import re
from pathlib import Path
import sys

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Routers to update (excluding auth.py which is already auth-aware)
ROUTERS = [
    "app/routers/sites.py",
    "app/routers/loads.py",
    "app/routers/carriers.py",
    "app/routers/agents.py",
    "app/routers/escalations.py",
    "app/routers/emails.py",
    "app/routers/snapshots.py",
    "app/routers/staleness.py",
    "app/routers/email_inbound.py",
]

def add_auth_import(content: str) -> str:
    """Add auth import if not already present."""
    if "from app.auth import" in content:
        print("  [OK] Auth import already present")
        return content

    # Find the last app import
    lines = content.split('\n')
    insert_index = None

    for i, line in enumerate(lines):
        if line.startswith('from app.'):
            insert_index = i + 1

    if insert_index:
        lines.insert(insert_index, 'from app.auth import get_current_user')
        print("  [OK] Added auth import")
        return '\n'.join(lines)

    print("  [WARN] Could not find app imports")
    return content


def add_user_import(content: str) -> str:
    """Add User model import if not already present."""
    if ", User" in content or "User," in content or "from app.models import User" in content:
        print("  [OK] User import already present")
        return content

    # Find app.models import and add User
    pattern = r'(from app\.models import .+?)(\n)'

    def replace_import(match):
        imports = match.group(1)
        if "User" not in imports:
            # Add User to the import list
            return imports + ', User' + match.group(2)
        return match.group(0)

    new_content = re.sub(pattern, replace_import, content)
    if new_content != content:
        print("  [OK] Added User to model imports")
    return new_content


def add_auth_to_endpoints(content: str) -> str:
    """Add current_user parameter to all endpoint functions."""

    # Pattern to match function definitions after @router decorators
    # Matches: def function_name(params, db: Session = Depends(get_db)):
    pattern = r'(@router\.(get|post|put|patch|delete)\([^\)]*\)[^\n]*\ndef\s+\w+\([^)]*db:\s*Session\s*=\s*Depends\(get_db\))(\))'

    def add_user_param(match):
        decorator_and_params = match.group(1)
        closing_paren = match.group(3)

        # Check if current_user already present
        if 'current_user' in decorator_and_params:
            return match.group(0)

        # Add current_user parameter before closing paren
        return decorator_and_params + ',\n    current_user: User = Depends(get_current_user)' + closing_paren

    new_content = re.sub(pattern, add_user_param, content, flags=re.MULTILINE)

    # Count how many endpoints were updated
    old_count = content.count('@router.')
    new_count = new_content.count('current_user: User = Depends(get_current_user)')

    if new_count > 0:
        print(f"  [OK] Added auth to {new_count} endpoints")

    return new_content


def update_router(file_path: str):
    """Update a single router file with authentication."""
    print(f"\nUpdating {file_path}...")

    path = Path(file_path)
    if not path.exists():
        print(f"  [ERROR] File not found: {file_path}")
        return

    content = path.read_text(encoding='utf-8')

    # Step 1: Add User import to models
    content = add_user_import(content)

    # Step 2: Add auth import
    content = add_auth_import(content)

    # Step 3: Add current_user to endpoints
    content = add_auth_to_endpoints(content)

    # Write back
    path.write_text(content, encoding='utf-8')
    print(f"  [OK] Saved {file_path}")


def main():
    print("=" * 60)
    print("Adding Authentication to API Routers")
    print("=" * 60)

    for router_file in ROUTERS:
        update_router(router_file)

    print("\n" + "=" * 60)
    print("[SUCCESS] Authentication added to all routers!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test endpoints with Postman or curl")
    print("2. Verify auth is required: GET /api/sites (should return 401)")
    print("3. Login first: POST /auth/login")
    print("4. Use token: GET /api/sites with Authorization: Bearer <token>")


if __name__ == "__main__":
    main()
