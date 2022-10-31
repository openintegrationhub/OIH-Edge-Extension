const consumers = [
    "influx",
    "mongodb",
    "webhook"]

const producers = [
    "opcua",
    "modbus",
    "mqtt",
    "iotsimulator",
    "iiotsimulator"
]

const streams = [
    "aggregator",
    "anonymizer",
    "data-logic-manager",
    "payperuse"
]

const component_category = Object.freeze({
    CONSUMERS: "consumers",
    PRODUCERS: "producers",
    STREAMS: "streams"
})

module.exports = {
    consumers,
    producers,
    streams,
    component_category
}