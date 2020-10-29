## Migration strategy from password to access codes

### Current situation

Test kits contain a tube with a random six-letter code, and a paper slip with the same code. When registering, the subject has to set a password. When querying the results, both barcode and password are needed.

### Planned scheme

Test kits contain a tube with a non-random barcode and a paper slip with a random 9-digit access code. When a test kit is packed, the association of the barcode to the access code is stored. To this end, the following precedure is used:

- A tube with a barcode is held against a scanner.

- A script with connection to the MongoDB data base verifies that the tube barcode does not exist in the data base, generates a random 9-digit code, verifies that this code does nto exist in the data base either

- The script adds a new document, with the tube barcode as title key, to the data base, and sets there the field "access_code" to the access code.

- The script prints a paper slip with the access code, and a QR code linking to, say, https://covidtest-hd.de/sample?access=nnnnnnnnn

- The printed slip is folded (to hide the code) and packed with the tube in a bag.

When registering a sample, the subject follows the QR code, or types in the URL, and selects "register test kit". If the QR code was used, the access code is prefilled, otherwise it has to be added. The fields to set a password will be removed.

When querying the result, the code is needed. Again, when using the QR code and the pressing "Enquire result", the access code field is pre-filled. The password field will no longer be present.

### Migration

- All already printed 6-letter codes are added to the data base using the 6-letter code as both bar code and access code.

- If a user registers an old test kit, he can enter the six-letter code as access code, and the registration will be correctly processed.

- If the user then queries the result, he can enter the six-letter code as access code. The result query page asks for the access code only. The password field will get removed.

- All already registered samples are transferred to the new server.

- Therefore, when querying a result, we need to check whether a "password hash" is set in one of the sample's registration records. If so, a message is displayed that this is an old sample, and we direct the user to a specific legacy page that asks for the password and checks it.
