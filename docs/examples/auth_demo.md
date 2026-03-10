# Auth Demo

Authentication and authorization demo with login, registration, role-based access, and admin panel.

## Features

- **LoginForm / RegisterForm**: Pre-built auth UI components
- **Cookie-based sessions**: Simple token-based authentication
- **`protected` decorator**: Page-level auth gating with redirect
- **UserMenu**: Dropdown menu with avatar and logout
- **RoleGuard**: Role-based conditional rendering (admin / editor / viewer)
- **AdminSite with auth_check**: Admin panel requiring authentication

## Run

```bash
uv run uvicorn examples.auth_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Demo Accounts

| Username | Role |
|---|---|
| Admin User | admin |
| Editor | editor |
| Viewer | viewer |

Any password works. You can also register a new account (assigned "viewer" role).

## Source

```python
--8<-- "examples/auth_demo.py"
```
