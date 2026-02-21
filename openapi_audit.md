# OpenAPI 2.0 vs 3.0/3.1 Audit for Parser Implementation

This document outlines key structural differences between OpenAPI versions that impact parsing logic, model generation, and server implementation.

## 1. Top-Level Structure
- **2.0:** Uses `swagger: "2.0"`.
- **3.0/3.1:** Uses `openapi: "3.0.x"` or `openapi: "3.1.x"`.
- **Primary Change:** The root object moved from a flat-ish layout to a grouped `components` object.

| Feature | OpenAPI 2.0 | OpenAPI 3.0/3.1 |
| :--- | :--- | :--- |
| **Global Host/Base** | `host`, `basePath`, `schemes` | `servers` (array of server objects) |
| **Definitions** | `definitions` | `components/schemas` |
| **Parameters** | `parameters` | `components/parameters` |
| **Security** | `securityDefinitions` | `components/securitySchemes` |
| **Request Bodies** | Part of `parameters` (in: body) | `requestBody` object |

## 2. Parameter & Body Differences (Critical for Parser)

### OpenAPI 2.0 (Swagger)
Payloads are just another parameter type (`in: body` or `in: formData`).
```yaml
paths:
  /pets:
    post:
      parameters:
        - name: pet
          in: body
          required: true
          schema:
            $ref: '#/definitions/Pet'
```

### OpenAPI 3.0/3.1
Bodies are separated from parameters into the `requestBody` field, supporting multiple media types.
```yaml
paths:
  /pets:
    post:
      requestBody:
        description: Pet to add
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Pet'
      parameters: 
        - name: tags
          in: query
          schema:
            type: array
            items:
              type: string
```

**Key Parser Change:** `parser.py` must check for `requestBody` in addition to looping through `parameters`. In 3.0, `parameters` still exists but **cannot** contain `in: body`.

## 3. Reference ($ref) Resolution
- **2.0:** Refs usually point to `#/definitions/...` or `#/parameters/...`.
- **3.0:** Refs point to `#/components/schemas/...`, `#/components/parameters/...`, etc.
- **3.1:** Supports `$ref` alongside sibling properties (e.g., you can add a `description` to a `$ref`). In 3.0, siblings are ignored.

## 4. Schema Differences
- **Required Fields:** Both 2.0 and 3.0 use a `required` array within the Schema object.
- **Nullable:** 
  - **2.0:** Not formally supported (vendor extensions used).
  - **3.0:** Use `nullable: true`.
  - **3.1:** Uses JSON Schema type arrays: `type: ["string", "null"]`.
- **Combined Schemas:**
  - **2.0:** No `oneOf` or `anyOf`. Only `allOf`.
  - **3.0/3.1:** Full support for `oneOf`, `anyOf`, `not`, and `allOf`.

## 5. Potential Breaks in `parser.py`

1.  **Missing `requestBody`:** If `parser.py` only iterates over `operation.get('parameters', [])`, it will fail to see the payload for POST/PUT/PATCH requests in OpenAPI 3.0.
2.  **Hardcoded `definitions` path:** If the parser looks for `#/definitions/`, it will fail on OpenAPI 3.0 which uses `#/components/schemas/`.
3.  **Media Type Nesting:** In 3.0, the schema is nested under `content/{media-type}/schema`. In 2.0, the schema is direct under the parameter.
4.  **$ref Siblings (3.1):** If the parser assumes `$ref` is the only key in an object, it may miss overrides or descriptions in 3.1.
5.  **Type Arrays (3.1):** If `parser.py` expects `type` to be a string, it will crash on 3.1's `type: ["string", "integer"]`.

## 6. Parsing Code Examples (Conceptual)

### Parsing 2.0 Body
```python
def get_body_schema_20(op):
    for p in op.get('parameters', []):
        if p.get('in') == 'body':
            return p.get('schema')
    return None
```

### Parsing 3.0 Body
```python
def get_body_schema_30(op):
    rb = op.get('requestBody', {})
    content = rb.get('content', {})
    # Generally pick the first media type or application/json
    for mt in ['application/json', 'multipart/form-data']:
        if mt in content:
            return content[mt].get('schema')
    return None
```
