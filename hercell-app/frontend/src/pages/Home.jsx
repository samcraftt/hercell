import Button from '../components/Button';
import { her2 } from '../api';
import { useAuth } from '../AuthContext';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { showErrorMessage } from '../utils/miscUtils';
import toast from 'react-hot-toast';

/** Border + fill for flagged-region overlays (index maps to region order from API). */
const regionHighlightPalette = [
  { border: '#d97706', fill: 'rgba(217, 119, 6, 0.22)', label: 'Amber' },
  { border: '#7c3aed', fill: 'rgba(124, 58, 237, 0.2)', label: 'Violet' },
  { border: '#059669', fill: 'rgba(5, 150, 105, 0.2)', label: 'Emerald' }
];

const Home = () => {
  const { logout, user } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [conventionalScore, setConventionalScore] = useState('0'); // This product is only for IHC score 0s, for now
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [question, setQuestion] = useState('');
  const [slideFile, setSlideFile] = useState(null);
  const [slidePreviewUrl, setSlidePreviewUrl] = useState(null);
  const [assistantAnswer, setAssistantAnswer] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!slideFile) {
      setSlidePreviewUrl(null);
      setAnalysis(null);
      return undefined;
    }

    const url = URL.createObjectURL(slideFile);
    setSlidePreviewUrl(url);
    setAnalysis(null);

    return () => URL.revokeObjectURL(url);
  }, [slideFile]);

  const handleAnalyzeSlide = async (e) => {
    e.preventDefault();
    if (!slideFile) {
      toast.error('Please upload a pathology slide image.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('conventionalScore', conventionalScore);
      formData.append('slideFile', slideFile);
      const nextAnalysis = await her2.analyzeSlide(formData);

      setAnalysis(nextAnalysis);
      setAssistantAnswer('');
      toast.success('Slide analysis complete.');
    } catch (error) {
      showErrorMessage(error, 'Failed to analyze slide, please try again.');
    }
    setIsAnalyzing(false);
  };

  const handleAskAssistant = async (e) => {
    e.preventDefault();
    if (!analysis) {
      toast.error('Please analyze a slide first.');
      return;
    }

    if (!question.trim()) {
      toast.error('Please enter a question for the assistant.');
      return;
    }

    setIsAsking(true);
    try {
      const answer = await her2.explainFinding({
        detectedExpression: analysis.detectedExpression,
        question
      });
      setAssistantAnswer(answer);
    } catch (error) {
      showErrorMessage(error, 'Failed to get assistant guidance.');
    }
    setIsAsking(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6 rounded-lg bg-white p-6 shadow">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">HER2 Ultralow Detector MVP</h1>
              <p className="mt-1 text-sm text-gray-600">
                {user
                  ? `Welcome, ${user.firstName}. Upload a HER2-stained slide and review flagged trace expression findings.`
                  : 'Decision support for pathologists who need a second look at borderline HER2 expression.'}
              </p>
            </div>
            {user ? (
              <Button
                onClick={logout}
                variant="secondary"
              >
                Log out
              </Button>
            ) : (
              <div className="flex flex-wrap gap-2">
                <Button onClick={() => navigate('/signup')} variant="primary">
                  Create account
                </Button>
                <Button onClick={() => navigate('/login')} variant="secondary">
                  Log in
                </Button>
              </div>
            )}
          </div>
        </div>

        {!user ? (
          <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 shadow-xl">
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 opacity-[0.12]"
              style={{
                backgroundImage:
                  'radial-gradient(circle at 1px 1px, rgb(255 255 255) 1px, transparent 0)',
                backgroundSize: '32px 32px'
              }}
            />
            <div className="relative px-6 py-14 sm:px-10 sm:py-16 lg:px-14 lg:py-20">
              <div className="mx-auto max-w-3xl text-center lg:mx-0 lg:max-w-none lg:text-left">
                <p className="text-sm font-medium uppercase tracking-widest text-indigo-300">
                  Pathology · IHC · HER2
                </p>
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl">
                  Catch ultralow HER2 the first pass can miss.
                </h2>
                <p className="mt-5 text-lg text-slate-300 sm:text-xl">
                  Hercell layers a secondary analysis on your digital slides—highlighting trace membrane
                  staining and singular-cell signals so you can document borderline cases with confidence.
                </p>
              </div>

              <div className="relative mt-14 grid gap-5 sm:grid-cols-2 lg:mt-16 lg:grid-cols-3">
                <div className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/30 text-lg font-semibold text-indigo-200">
                    1
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-white">Secondary scan</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-300">
                    Upload a stained slide and run analysis tuned for expression below conventional IHC
                    scoring cutoffs.
                  </p>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/30 text-lg font-semibold text-violet-200">
                    2
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-white">Flagged foci</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-300">
                    Review candidate regions with coordinates and confidence so nothing subtle slips
                    through sign-out.
                  </p>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm sm:col-span-2 lg:col-span-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/25 text-lg font-semibold text-cyan-200">
                    3
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-white">Report-ready language</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-300">
                    Draft addenda and workflow prompts you can reconcile with morphology—built for
                    multidisciplinary review, not black-box calls.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="grid gap-6 lg:grid-cols-2">
              <section className="rounded-lg bg-white p-6 shadow">
                <h2 className="text-lg font-semibold text-gray-900">1) Upload and Analyze Slide</h2>
                <p className="mt-1 text-sm text-gray-600">
                  Designed for pathologists to detect HER2 expression below conventional thresholds.
                </p>
                <form className="mt-5 space-y-4" onSubmit={handleAnalyzeSlide}>
                  <div>
                    <label className="block text-sm font-medium text-gray-700" htmlFor="slide-file">
                      Digital slide image
                    </label>
                    <input
                      accept="image/*"
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      id="slide-file"
                      onChange={(e) => setSlideFile(e.target.files?.[0] || null)}
                      type="file"
                    />
                  </div>
                  {slidePreviewUrl && (
                    <div className="space-y-3">
                      <div className="relative w-full max-w-full overflow-hidden rounded-lg border border-gray-200 bg-gray-900/5 shadow-inner">
                        <img
                          alt={slideFile ? `Preview of ${slideFile.name}` : 'Selected slide'}
                          className="block h-auto w-full object-contain"
                          decoding="async"
                          src={slidePreviewUrl}
                        />
                        {analysis?.flaggedRegions.map((region, index) => {
                          const palette = regionHighlightPalette[index % regionHighlightPalette.length];
                          const size = 'clamp(4.5rem, 16vmin, 7.5rem)';
                          return (
                            <div
                              aria-hidden
                              className="pointer-events-none absolute rounded-full"
                              key={region.id}
                              style={{
                                backgroundColor: palette.fill,
                                border: `3px solid ${palette.border}`,
                                boxShadow: `0 0 0 1px rgba(255,255,255,0.85), 0 0 24px ${palette.border}55`,
                                height: size,
                                left: `${region.x}%`,
                                top: `${region.y}%`,
                                transform: 'translate(-50%, -50%)',
                                width: size
                              }}
                            />
                          );
                        })}
                      </div>
                    </div>
                  )}
                  <Button className="w-full" disabled={isAnalyzing} type="submit">
                    {isAnalyzing ? 'Analyzing...' : 'Run Secondary HER2 Analysis'}
                  </Button>
                </form>
              </section>

              <section className="rounded-lg bg-white p-6 shadow">
                <h2 className="text-lg font-semibold text-gray-900">2) Review Detection Results</h2>
                {!analysis ? (
                  <p className="mt-4 text-sm text-gray-600">
                    No analysis yet. Upload a slide to see flagged regions and report-ready interpretation.
                  </p>
                ) : (
                  <div className="mt-4 space-y-4 text-sm">
                    <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
                      <p><span className="font-medium">Model:</span> {analysis.modelVersion}</p>
                      <p>
                        <span className="font-medium">Detected ultralow HER2:</span>{' '}
                        {analysis.detectedExpression ? 'Yes' : 'No'}
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Flagged regions</h3>
                      <ul className="mt-2 space-y-2">
                        {analysis.flaggedRegions.map((region, index) => {
                          const palette = regionHighlightPalette[index % regionHighlightPalette.length];
                          return (
                            <li
                              className="rounded-md border border-gray-200 border-l-4 bg-white p-3"
                              key={region.id}
                              style={{ borderLeftColor: palette.border }}
                            >
                              <p className="font-medium">{region.id} — confidence {region.confidence}%</p>
                              <p className="text-gray-600">{region.notes}</p>
                              <p className="text-gray-500">Map position: {region.x}%, {region.y}%</p>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                    <div className="rounded-md border border-blue-200 bg-blue-50 p-3">
                      <h3 className="font-medium text-blue-900">Suggested report addendum</h3>
                      <p className="mt-1 text-blue-900">{analysis.interpretation.addendum}</p>
                      <p className="mt-1 text-blue-800">{analysis.interpretation.recommendation}</p>
                    </div>
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Home;
