// Import all your needs
const utils = require('./src/v1/utils/utils')

const express = require('express')
const app = express()
const dotenv = require('dotenv');
dotenv.config();

const consumersv1 = require('./src/v1/consumers');
const producersv1 = require('./src/v1/producers');
const streamsv1 = require('./src/v1/streams');
const clusterv1 = require('./src/v1/kafka_cluster')

app.use(express.json());
app.use(express.urlencoded());
app.use('/api/v1/consumers', consumersv1)
app.use('/api/v1/producers', producersv1)
app.use('/api/v1/streams', streamsv1)
app.use('/api/v1/kafka_cluster', clusterv1)

utils.createCluster(null, null, null, null, console.log, console.log)

const PORT = 8069
const HOST = '0.0.0.0'
app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`)
