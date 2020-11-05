function decrypt(data, privateKeyPem, password) {
	var privateKey;
	if(password)
		privateKey = forge.pki.decryptRsaPrivateKey(privateKeyPem, password)
	else 
		privateKey = forge.pki.privateKeyFromPem(privateKeyPem);

	Object.keys(data).forEach(key => {
		data[key] = forge.util.decode64(data[key]);
	});

	var session_key = privateKey.decrypt(data.session_key_encrypted, "RSAES-OAEP");	
	//console.log(forge.util.encode64(session_key));

	var encrypted_fields = ["name", "address", "contact"];

	var decipher = forge.cipher.createDecipher('AES-CBC', session_key);
	decipher.start({iv: data.aes_instance_iv});
	encrypted_fields.forEach(el => {
		decipher.update(forge.util.createBuffer(data[el + "_encrypted"]));
	})
	
	var output = decipher.output.toString();
	console.log(decipher.finish());

	var result = {};
	var i = 0;
	encrypted_fields.forEach(el => {
		result[el] = output
			.slice(i, i + data[el + "_encrypted"].length)
			.replace(/\0/g, '');
		i += data[el + "_encrypted"].length;
	});

	return result;
}