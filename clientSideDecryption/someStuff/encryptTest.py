import json

exec(open("../covidtest/app/encryption_helper.py").read())
key = rsa_instance_from_key(open("src/public_32c865.pem").read())
res = encrypt_subject_data(key, "Some guy", "Wierd town, Elm Street 13", "email@somewhere.com")

with open("src/encr_data.json", "w") as out:
	out.write(json.dumps(res, sort_keys=True, indent=4))