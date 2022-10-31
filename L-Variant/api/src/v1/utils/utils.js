const { spawn } = require('child_process');
const { component_category, consumers, producers, streams } = require('./dictionary.js')
const fs = require("fs")

/**
 * Executes a python script to start a new kafka cluster or if
 * only certain services of the cluster
 * @param { list } services kafka services: zookeeper, broker, kafka-ui
 * @param { int } zp port for the zookeeper8
 * @param { list } bp ports for the broker
 * @param { int } kp port for the ui
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function createCluster(services, zp, bp, kp, callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.KAFKA)
        args.push(clusterDic.COMMAND)
        args.push(clusterManagementDic.UP)
        if (services !== undefined && services !== null) {
            args.push(clusterDic.SERVICE)
            args.push(services)
        }
        if (zp !== undefined && zp !== null) {
            args.push(clusterDic.ZOOKEEPER)
            args.push(zp)
        }
        if (bp !== undefined && bp !== null) {
            args.push(clusterDic.BROKER)
            args.push(bp)
        }
        if (kp !== undefined && kp !== null) {
            args.push(clusterDic.KAFKAUI)
            args.push(kp)
        }

        const python = spawn('python', args);
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Retrieve the status of the kafka cluster
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function getClusterStatus(callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.KAFKA)
        args.push(clusterDic.COMMAND)
        args.push(clusterManagementDic.STATUS)

        const python = spawn('python', args)
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Manages the cluster depending on the given command
 * @param { list } services kafka services: zookeeper, broker, kafka-ui
 * @param { string } command management command
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function clusterManagement(services, command, callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.KAFKA)
        args.push(clusterDic.COMMAND)
        args.push(command)

        if (command !== "DOWN" && services !== undefined) {
            args.push(clusterDic.SERVICE)
            args.push(services)
        }

        const python = spawn('python', args)
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Manage docker containers depending on the given command
 * @param { string } id Container id
 * @param { string } command management command
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 * @returns 
 */
function containerManagement(id, command, callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.MANAGER)
        args.push(id)
        args.push(command)

        const python = spawn('python', args);
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Return a list of all running container with the given component type
 * @param { string } component_type component type either stream, producer or consumer
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function getList(component_type, callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.LIST)
        args.push("True")
        args.push(component_type)

        const python = spawn('python', args);
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Create a new container depending on the given component
 * @param { string } type Component
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function createContainer(type, callbackFunc, errCallbackFunc) {
    try {
        const args = []
        args.push(scriptDic.CREATE)
        args.push(type)

        const python = spawn('python', args);
        readScript(python, callbackFunc, errCallbackFunc)

    } catch (error) {
        errCallbackFunc(error)
    }
    return
}

/**
 * Create a new or update a config file by id
 * @param { string } id container id
 * @param { object } config config for the container
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function writeConfig(id, config, callbackFunc, errCallbackFunc) {
    containerManagement(
        id,
        commandDic.GET_PATHNAME,
        path_name => {
            var category = null

            if (matchesCategory(component_category.CONSUMERS, path_name))
                category = "consumers"

            if (matchesCategory(component_category.PRODUCERS, path_name))
                category = "producers"

            if (matchesCategory(component_category.STREAMS, path_name))
                category = "streams"

            const component = path_name.toString().split("_")[0]
            const folderPath = `.././${category}/${component}/config/${path_name}`
            fs.mkdir(folderPath, { recursive: true }, (err) => {
                if (err)
                    return errCallbackFunc(err)

                console.log("mkdir: " + err)
            });

            fs.writeFile(folderPath + '/config.json', JSON.stringify(config), function (err) {
                if (err)
                    return errCallbackFunc(err)

                console.log("writefile: " + err)

                return callbackFunc(config)
            });
        },
        err => {
            console.log("container management: " + err)

            errCallbackFunc(err)
        }
    )
}

/**
 * Execute a python script and callback its output
 * @param {*} script Executable python script
 * @param {*} callbackFunc callback function
 * @param {*} errCallbackFunc error callback function
 */
function readScript(script, callbackFunc, errCallbackFunc) {
    var res = null
    script.stdout.on('data', (data) => {
        console.log(data.toString())
        res = data
    });
    script.stdout.on('close', (err) => {
        if (res == null)
            errCallbackFunc(err)
        else
            callbackFunc(res)
        return
    })

    script.on('error', (err) => {
        console.error('Failed to start subprocess.');
        errCallbackFunc(err)
        return
    });
    return
}

/**
 * Check if the given value matches to the given category
 * @param { object } category 
 * @param { string } value
 * @returns bool
 */
function matchesCategory(category, value) {
    console.log(value)
    switch (category) {
        case component_category.CONSUMERS:
            return consumers.some(consumer => value.includes(consumer))
        case component_category.PRODUCERS:
            return producers.some(producer => value.includes(producer))
        case component_category.STREAMS:
            return streams.some(stream => value.includes(stream))
        default:
            return false
    }
}

const scriptDic = Object.freeze({
    LIST: "./src/v1/scripts/container_list.py",
    MANAGER: "./src/v1/scripts/container_management.py",
    CREATE: "./src/v1/scripts/new_containers.py",
    KAFKA: "./src/v1/scripts/kafka_cluster.py"
});

const commandDic = Object.freeze({
    START: "start",
    STOP: "stop",
    RESTART: "restart",
    PAUSE: "pause",
    UNPAUSE: "unpause",
    REMOVE: "remove",
    GET: "get",
    GET_PATHNAME: "getPathname"
});

const clusterDic = Object.freeze({
    ZOOKEEPER: "-zp",
    BROKER: "-bp",
    KAFKAUI: "-kp",
    SERVICE: "-s",
    COMMAND: "-c"
})

const clusterManagementDic = Object.freeze({
    START: "start",
    STOP: "stop",
    UP: "up",
    DOWN: "down",
    REMOVE: "remove",
    PAUSE: "pause",
    UNPAUSE: "unpause",
    RESTART: "restart",
    STATUS: "status"
})

module.exports = {
    getList,
    containerManagement,
    createContainer,
    scriptDic,
    matchesCategory,
    commandDic,
    createCluster,
    clusterManagement,
    clusterManagementDic,
    getClusterStatus,
    writeConfig
}