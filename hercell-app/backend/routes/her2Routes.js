const express = require('express');
const her2Controller = require('../controllers/her2Controller');
const multer = require('multer');

const router = express.Router();
const upload = multer({
  limits: {
    fileSize: 10 * 1024 * 1024
  },
  storage: multer.memoryStorage()
});

router.post('/analyze', upload.single('slideFile'), her2Controller.analyzeSlide);
router.post('/explain', her2Controller.explainFinding);

module.exports = router;
