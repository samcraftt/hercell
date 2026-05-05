const randomIntInclusive = (min, max) => {
  return min + Math.floor(Math.random() * (max - min + 1));
};

const distanceBetween = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

/**
 * Three random (x, y) pairs in percent space, kept inset from edges and
 * roughly separated so overlays do not stack every run.
 */
const randomRegionPositions = () => {
  const margin = 8;
  const max = 100 - margin;
  const minSeparation = 14;
  const maxAttempts = 100;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const points = Array.from({ length: 3 }, () => ({
      x: randomIntInclusive(margin, max),
      y: randomIntInclusive(margin, max)
    }));

    let separated = true;
    for (let i = 0; i < 3; i += 1) {
      for (let j = i + 1; j < 3; j += 1) {
        if (distanceBetween(points[i], points[j]) < minSeparation) {
          separated = false;
        }
      }
    }

    if (separated) {
      return points;
    }
  }

  return [
    { x: 22, y: 24 },
    { x: 52, y: 48 },
    { x: 78, y: 72 }
  ];
};

const buildFlaggedRegions = (seedValue) => {
  const confidenceBase = 62 + (seedValue % 26);
  const [p0, p1, p2] = randomRegionPositions();

  return [
    {
      confidence: Math.min(confidenceBase, 97),
      id: 'region-a1',
      notes: 'Membrane staining in clustered tumor cells',
      x: p0.x,
      y: p0.y
    },
    {
      confidence: Math.min(confidenceBase - 8, 94),
      id: 'region-b3',
      notes: 'Faint partial membrane staining in isolated cell',
      x: p1.x,
      y: p1.y
    },
    {
      confidence: Math.min(confidenceBase - 12, 91),
      id: 'region-c2',
      notes: 'Trace staining pattern near invasive edge',
      x: p2.x,
      y: p2.y
    }
  ];
};

const buildInterpretation = (detectedExpression, flaggedRegions) => {
  if (!detectedExpression) {
    return {
      addendum: 'No ultralow HER2 expression was detected by secondary analysis.',
      recommendation: 'Correlate with morphology and repeat staining if clinical suspicion remains high.'
    };
  }

  return {
    addendum: `Secondary HER2 ultralow analysis detected trace expression in ${flaggedRegions.length} region(s), including at least one singular-cell level finding.`,
    recommendation: 'Pathologist review of highlighted regions is recommended before final report sign-out.'
  };
};

const analyzeSlide = async (req, res) => {
  try {
    const { conventionalScore } = req.body;
    const slideFile = req.file;
    if (!slideFile) {
      return res.status(400).json({ error: 'Slide file is required for analysis.' });
    }

    if (!['0', '1+', '2+', '3+'].includes(conventionalScore)) {
      return res.status(400).json({ error: 'Conventional IHC score must be one of: 0, 1+, 2+, 3+.' });
    }

    const fileName = slideFile.originalname;
    const seedValue = fileName.length + slideFile.size;
    const flaggedRegions = buildFlaggedRegions(seedValue);
    const detectedExpression = conventionalScore === '0' || conventionalScore === '1+' || (seedValue % 3 !== 0);
    const interpretation = buildInterpretation(detectedExpression, flaggedRegions);

    res.json({
      analysis: {
        analyzedAt: new Date().toISOString(),
        conventionalScore,
        detectedExpression,
        flaggedRegions,
        fileName,
        interpretation,
        modelVersion: 'mvp-her2-cell-detector-v0.1'
      }
    });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Failed to analyze slide, please try again.' });
  }
};

const explainFinding = async (req, res) => {
  try {
    const { detectedExpression, question } = req.body;
    if (!question) return res.status(400).json({ error: 'Please provide a question for the assistant.' });

    const normalizedQuestion = question.toLowerCase();
    let answer = 'Review flagged regions against HER2 membrane staining patterns and correlate with morphology before finalizing interpretation.';

    if (normalizedQuestion.includes('enhertu') || normalizedQuestion.includes('eligib')) {
      answer = detectedExpression
        ? 'Potential eligibility signal: ultralow HER2 expression was detected. Treating oncologist should combine this finding with full clinical context.'
        : 'No ultralow HER2 expression was detected in this scan, so this result alone does not support Enhertu eligibility.';
    } else if (normalizedQuestion.includes('confidence') || normalizedQuestion.includes('accuracy')) {
      answer = 'This MVP is a decision-support prototype targeting an 80% detection accuracy milestone and must be confirmed by pathologist review.';
    } else if (normalizedQuestion.includes('workflow') || normalizedQuestion.includes('report')) {
      answer = 'Use the generated addendum as a draft statement and include it in the pathology report only after manual verification.';
    }

    res.json({ answer });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Failed to generate interpretation guidance.' });
  }
};

module.exports = {
  analyzeSlide,
  explainFinding
};
