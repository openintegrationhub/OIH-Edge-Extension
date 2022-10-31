const auth = require('basic-auth')

const getAuthorizer = (name, pass) => (req, res, next) => {
    const user = auth(req)
    if (!user || user.name !== name || user.pass !== pass)
        return res.status(401).send('Unauthorized')

    next()
}

const admin = getAuthorizer('admin', 'xinsecret')

module.exports = { admin }