const router = require('express').Router()
const controller = require('./controller')
const auth = require('../middlewares/auth')

router.get('/', auth.admin, controller.getAll)
router.post('/', auth.admin, controller.create)
router.post('/:id/start', auth.admin, controller.start)
router.post('/:id/stop', auth.admin, controller.stop)
router.post('/:id/config', auth.admin, controller.update)
router.get('/:id', auth.admin, controller.getById)
router.delete('/:id', auth.admin, controller.remove)

module.exports = router