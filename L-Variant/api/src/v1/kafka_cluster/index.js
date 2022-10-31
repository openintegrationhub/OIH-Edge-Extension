const router = require('express').Router()
const controller = require('./controller')

router.get('/', controller.getStatus)
router.post('/', controller.createClusterServices)
router.post('/start', controller.start)
router.post('/stop', controller.stop)
router.post('/pause', controller.pause)
router.post('/unpause', controller.unpause)
router.post('/restart', controller.restart)
router.delete('/down', controller.down)
router.delete('/remove', controller.remove)

module.exports = router