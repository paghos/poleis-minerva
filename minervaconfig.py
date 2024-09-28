#Set here the OAUTH credentials :)
appConf = {
    "OAUTH2_CLIENT_ID": "minerva",
    "OAUTH2_CLIENT_SECRET": "oauth-secret",
    "OAUTH2_ISSUER": "https://id.server.url/realms/cerberus",
    "FLASK_SECRET": "random-string",
}

database = {
    "DATABASE_CONFIG":"mysql+mysqlconnector://dbuser:dbpass@10.10.10.10:3308/minerva_demo"
}

ai = {
    "MINERVA_AI_ENDPOINT":"http://endpoint-ai.lan.paganosimone.com:5050/upload",
    "MINERVA_AI_TOKEN":"ADD_HERE_THE_MINERVA_AI_LICENSE_TOKEN_FOR_THE_PAID_VERSION",
    "MINERVA_AI_INSTANCE_NAME":"ComuneDiMacondo"
}