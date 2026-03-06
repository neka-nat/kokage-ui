# Model Components

Auto-generated UI from Pydantic models. These inspect model fields to create forms, tables, and detail views automatically.

## ModelForm

Auto-generated form from a Pydantic model.

### Preview

<iframe src="../previews/modelform.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(title="Name")
    email: str = Field(title="Email")
    age: int = Field(default=20, title="Age", ge=0, le=150)

ModelForm(User, action="/users", submit_text="Create User")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `type[BaseModel]` | Pydantic model class |
| `action` | `str` | Form action URL |
| `method` | `str` | HTTP method (default: "post") |
| `submit_text` | `str` | Submit button text (default: "Submit") |
| `exclude` | `set[str] | None` | Fields to exclude |
| `instance` | `BaseModel | None` | Pre-fill instance for editing |

---

## ModelTable

Auto-generated table from Pydantic model instances.

### Preview

<iframe src="../previews/modeltable.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
ModelTable(
    User,
    rows=[
        User(name="Alice", email="alice@example.com", age=30),
        User(name="Bob", email="bob@example.com", age=25),
    ],
    zebra=True,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `type[BaseModel]` | Pydantic model class |
| `rows` | `list[BaseModel]` | Data rows |
| `zebra` | `bool` | Zebra striping |
| `compact` | `bool` | Compact size |
| `exclude` | `set[str] | None` | Fields to exclude |

---

## ModelDetail

Detail card showing a single model instance.

### Preview

<iframe src="../previews/modeldetail.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
ModelDetail(
    User(name="Alice", email="alice@example.com", age=30),
    title="User Profile",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `instance` | `BaseModel` | Model instance to display |
| `title` | `str | None` | Card title |
| `exclude` | `set[str] | None` | Fields to exclude |

---
