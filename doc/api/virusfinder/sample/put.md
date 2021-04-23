# Update Sample

Once a sample is ready to be send, this API call is used to update the 
sample with its unique barcode.

## Request

**URL** : `/api/virusfinder/sample`

**Method** : `PUT`

**Auth required** : YES

**Permissions required** : None

### DTO:
All fields must be sent.

```json
{
  "auth": {
    "username": "Testuser", 
    "password": "*******"
  },
  "access_code": "123456789",
  "barcode": "123456789"
}
```

## Success Response

**Code** : `204 NO CONTENT`

### DTO:

```json
{}
```

## Error Responses
**Condition** : Authentication failed

**Code** : `401 Unauthorized`

### DTO:
````json
{}
````

### Or

**Condition** : Something went wrong. More information in error message.

**Code** : `400 Bad Request `

### DTO:
````json
{"error": "error message"}
````
