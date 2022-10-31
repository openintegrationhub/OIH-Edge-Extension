const { getList, containerManagement, createContainer, commandDic, matchesCategory, writeConfig } = require('../utils/utils.js')
const { component_category, consumers } = require('../utils/dictionary.js')

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
    create,
    start,
    stop,
    getById,
    update,
    remove,
    getAll
}

/**
 * Creates a new image
 * @param {request} req Request
 * @param {*} res Response
 */
function create(req, res) {
    if (req.query.type == null || req.query.type == undefined)
        return res.status(400).send()

    const reqType = req.query.type
    const typeIndex = consumers.indexOf(reqType)
    const type = consumers[typeIndex]

    if (type == undefined)
        return res.status(400).send()

    createContainer(
        type,
        data => res.status(200).send(data),
        err => res.status(400).send(err)
    )
    return
}

/**
 * Returns one instance by id
 * @param {request} req Request
 * @param {*} res Response
 */
function getById(req, res) {
    try {
        const id = req.params.id
        containerManagement(
            id,
            commandDic.GET,
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
 * Starts an instance by id
 * @param {request} req Request
 * @param {*} res Response
 */
function start(req, res) {
    try {
        const id = req.params.id
        containerManagement(
            id,
            commandDic.START,
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
 * Stops an instance by id
 * @param {request} req Request
 * @param {*} res Response
 */
function stop(req, res) {
    try {
        const id = req.params.id
        containerManagement(
            id,
            commandDic.STOP,
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
 * Updates a config by id
 * @param {request} req Request
 * @param {*} res Response
 */
function update(req, res) {
    const id = req.params.id
    writeConfig(id, req.body, data => res.status(200).send(data), err => res.status(500).send(err))
    return
}


/**
 * Removes instance by id
 * @param {request} req Request
 * @param {*} res Response
 */
function remove(req, res) {
    try {
        const id = req.params.id
        containerManagement(
            id,
            commandDic.REMOVE,
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
 * Returns all consumers
 * @param {request} req Request
 * @param {*} res Response
 */
function getAll(req, res) {
    try {
        getList(
            component_category.CONSUMERS,
            data => {
                res.status(200).send(data)
            },
            err => {
                console.log(err)
                res.status(400).send(err)
            }
        )
        return
    } catch (error) {
        return res.status(500).send(error)
    }
}