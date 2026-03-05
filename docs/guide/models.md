# Pydantic Models → UI

kokage-ui can auto-generate forms, tables, and detail views from Pydantic `BaseModel` definitions. Field types, constraints, and metadata are used to select appropriate HTML input types.

## ModelForm

Generates a DaisyUI-styled `<form>` from a Pydantic model.

```python
from pydantic import BaseModel, Field
from kokage_ui import ModelForm

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, le=150, default=30)
    is_active: bool = True

ModelForm(User, action="/users", method="post")
```

### Type → Input Mapping

| Python Type | HTML Input | Notes |
|-------------|-----------|-------|
| `str` | `<input type="text">` | Default for strings |
| `str` (name contains "email") | `<input type="email">` | Heuristic |
| `str` (name contains "password") | `<input type="password">` | Heuristic |
| `str` (long max_length or name like "bio") | `<textarea>` | Heuristic: max_length > 200 or name in bio/description/etc. |
| `int` | `<input type="number" step="1">` | |
| `float` | `<input type="number" step="any">` | |
| `bool` | `<input type="checkbox">` | |
| `Literal["a", "b"]` | `<select>` | Options from literal values |
| `Enum` | `<select>` | Options from enum members |

### Constraint → HTML Attribute Mapping

| Pydantic Constraint | HTML Attribute |
|--------------------|----------------|
| `Field(min_length=N)` | `minlength="N"` |
| `Field(max_length=N)` | `maxlength="N"` |
| `Field(ge=N)` | `min="N"` |
| `Field(le=N)` | `max="N"` |
| `Field(gt=N)` | `min="N"` |
| `Field(lt=N)` | `max="N"` |
| `Field(pattern=r"...")` | `pattern="..."` |

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | type[BaseModel] | Pydantic model class |
| `action` | str | Form action URL |
| `method` | str | HTTP method (default: `"post"`) |
| `submit_text` | str | Submit button text (default: `"Submit"`) |
| `submit_color` | str | DaisyUI color for submit button (default: `"primary"`) |
| `exclude` | set \| list \| None | Field names to exclude |
| `include` | set \| list \| None | Only include these fields |
| `instance` | BaseModel \| None | Pre-fill with instance values (edit mode) |
| `values` | dict \| None | Dict of field values to restore (after validation failure) |
| `errors` | list[dict] \| None | Pydantic ValidationError dicts for inline error display |

### Edit Mode

Pass an `instance` to pre-fill the form with existing values:

```python
user = User(name="Alice", email="alice@example.com", age=30, is_active=True)

ModelForm(User, action="/users/1/edit", method="post", instance=user)
```

### Validation Errors

Pass `errors` from a Pydantic `ValidationError` to show inline error messages:

```python
from pydantic import ValidationError

try:
    user = User.model_validate(form_data)
except ValidationError as e:
    form = ModelForm(
        User,
        action="/users",
        values=form_data,       # Restore entered values
        errors=e.errors(),      # Show error messages
    )
```

## ModelTable

Generates a DaisyUI-styled table from a model definition and a list of instances.

```python
from kokage_ui import ModelTable

users = [
    User(name="Alice", email="alice@example.com", age=30, is_active=True),
    User(name="Bob", email="bob@example.com", age=25, is_active=False),
]

ModelTable(User, rows=users, zebra=True)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | type[BaseModel] | Pydantic model class |
| `rows` | list[BaseModel] | List of model instances |
| `exclude` | set \| list \| None | Field names to exclude |
| `include` | set \| list \| None | Only include these fields |
| `zebra` | bool | Zebra striping |
| `compact` | bool | Compact size |
| `cell_renderers` | dict[str, Callable] | Custom `field_name → callable(value)` renderers |
| `extra_columns` | dict[str, Callable] | Extra columns: `header → callable(row)` |

### Custom Cell Renderers

Override how specific fields are displayed:

```python
from kokage_ui import A, Badge

ModelTable(
    User,
    rows=users,
    cell_renderers={
        "email": lambda v: A(v, href=f"mailto:{v}"),
        "is_active": lambda v: Badge("Active", color="success") if v else Badge("Inactive", color="error"),
    },
)
```

### Extra Columns

Add columns that aren't part of the model:

```python
ModelTable(
    User,
    rows=users,
    extra_columns={
        "Actions": lambda row: A("Edit", href=f"/users/{row.id}/edit", cls="btn btn-sm"),
    },
)
```

## ModelDetail

Generates a card-based detail view from a model instance.

```python
from kokage_ui import ModelDetail

user = User(name="Alice", email="alice@example.com", age=30, is_active=True)
ModelDetail(user, title="User Details")
```

Each field is displayed as a label-value pair inside a `Card` component. Boolean values are rendered as colored `Badge` components.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instance` | BaseModel | Pydantic model instance |
| `exclude` | set \| list \| None | Field names to exclude |
| `include` | set \| list \| None | Only include these fields |
| `title` | str \| None | Card title (defaults to model class name) |
