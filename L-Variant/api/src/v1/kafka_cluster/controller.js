const { clusterManagement, clusterManagementDic, createCluster, getClusterStatus } = require('../utils/utils.js')

/**
 * GET      /api/v1/consumers               -> getAll
 * POST     /api/v1/consumers/              -> create
 * POST      /api/v1/consumers/:id/start    -> start
 * POST      /api/v1/consumers/:id/stop     -> stop
 * GET      /api/v1/consumers/:id           -> getById
 * PUT      /api/v1/consumers/:id/config    -> update
 * DELETE   /api/v1/consumers/:id           -> remove
 */

module.exports = {
    createClusterServices,
    start,
    stop,
    pause,
    unpause,
    restart,
    remove,
    down,
    getStatus
}

/**
 * Creates a new kafka cluster
 * @param {request} req Request
 * @param {*} res Response
 */
function createClusterServices(req, res) {
    try {
        const services = req.query.services
        const zp = req.query.zookeeper_ports
        const bp = req.query.broker_ports
        const kp = req.query.kafkaui_ports
        createCluster(
            services,
            zp,
            bp,
            kp,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Starts an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function start(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.START,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Stops an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function stop(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.STOP,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Removes instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function remove(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.REMOVE,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Pauses an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function pause(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.PAUSE,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Unpauses an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function unpause(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.UNPAUSE,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Restart an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function restart(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            services,
            clusterManagementDic.RESTART,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Remove and shutdown an instance by service
 * @param {request} req Request
 * @param {*} res Response
 */
function down(req, res) {
    try {
        const services = req.query.services
        clusterManagement(
            null,
            clusterManagementDic.DOWN,
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}

/**
 * Return the status of the corresponding service.
 * @param {request} req Request
 * @param {*} res Response
 */
function getStatus(req, res) {
    try {
        getClusterStatus(
            data => res.status(200).send(data),
            err => res.status(400).send(err)
        )
        return
    } catch (error) {
        console.log(error)
        return res.status(500).send(error)
    }
}