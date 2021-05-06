# Create Sample

Creates a Sample, Recipient and associates it with a bag

## Request

**URL** : `/api/virusfinder/sample`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : None

### DTO:
All fields must be sent.

Auth
```json
{
  "username": "Testuser", 
  "password": "*******"
}
```
Body //  TODO Body ignored for now
```json
{
//  "name": "Mustermann, Max",
//  "address": "Musterstraße 1, 12345 Musterstadt",
//  "telephone": "0123456789"
}
```

## Success Response

**Code** : `201 CREATED`

### DTO:

```json
{
    "access_code": "123456789"
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
