
// mongodb.js
const { MongoClient } = require("mongodb");
const uri = "mongodb+srv://kullanici:sifre@cluster.mongodb.net/otomarket?retryWrites=true&w=majority";
const client = new MongoClient(uri);
module.exports = client;
