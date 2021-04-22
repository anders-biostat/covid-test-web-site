# Create Sample

Creates a Sample, Recipient and associates it with a bag

## Request

**URL** : `/api/virusfinder/sample`

**Method** : `POST`

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
  "name": "",
  "address": "",
  "telephone": ""
}
```

## Success Response

**Code** : `201 CREATED`

### DTO:

```json
{
    "access_code": 6546541685
}
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
