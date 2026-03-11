import React, { useState } from "react";
import TierSelector from "./components/TierSelector.jsx";
import FileUpload from "./components/FileUpload.jsx";
import ColumnMapper from "./components/ColumnMapper.jsx";
import ProgressBar from "./components/ProgressBar.jsx";
import ResultsTable from "./components/ResultsTable.jsx";
import ExportButton from "./components/ExportButton.jsx";
import {
  uploadSalesforce,
  uploadMatchFile,
  startMatch,
  subscribeProgress,
  fetchResults,
} from "./api.js";

const STEPS = [
  { id: 1, label: "Choose Tier" },
  { id: 2, label: "Salesforce Export" },
  { id: 3, label: "Matching File" },
  { id: 4, label: "Run Matching" },
  { id: 5, label: "Results" },
];

const REQUIRED_MAPPINGS = {
  1: ["org_nr"],
  2: ["company_name", "city"],
  3: ["company_name"],
};

function Stepper({ current }) {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((step, i) => {
          const isDone = step.id < current;
          const isCurrent = step.id === current;
          return (
            <li key={step.id} className={`flex items-center ${i < STEPS.length - 1 ? "flex-1" : ""}`}>
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  isDone
                    ? "bg-blue-500 text-white"
                    : isCurrent
                    ? "bg-blue-500 text-white ring-4 ring-blue-100"
                    : "bg-gray-200 text-gray-500"
                }`}>
                  {isDone ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : step.id}
                </div>
                <span className={`text-sm font-medium hidden sm:block ${isCurrent ? "text-blue-600" : isDone ? "text-gray-700" : "text-gray-400"}`}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 mx-3 transition-colors ${isDone ? "bg-blue-500" : "bg-gray-200"}`} />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function Card({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {(title || subtitle) && (
        <div className="px-8 py-6 border-b border-gray-100">
          {title && <h2 className="text-xl font-semibold text-gray-900">{title}</h2>}
          {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
        </div>
      )}
      <div className="px-8 py-6">{children}</div>
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState(1);
  const [tier, setTier] = useState(null);
  const [sfData, setSfData] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [mappings, setMappings] = useState({});
  const [progress, setProgress] = useState({ processed: 0, total: 0, done: false });
  const [progressError, setProgressError] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSfUpload(file) {
    const data = await uploadSalesforce(file);
    setSfData({ name: file.name, rowCount: data.row_count, preview: data.preview, columns: data.columns });
  }

  async function handleMatchUpload(file) {
    const data = await uploadMatchFile(file);
    setMatchData({ name: file.name, rowCount: data.row_count, preview: data.preview, columns: data.columns });
    setMappings({});
  }

  function isMappingComplete() {
    const required = REQUIRED_MAPPINGS[tier] || [];
    return required.every((k) => mappings[k]);
  }

  async function handleRunMatch() {
    setIsLoading(true);
    setProgressError(null);
    setProgress({ processed: 0, total: 0, done: false });
    setResults(null);
    setStep(4);

    try {
      await startMatch(tier, mappings);
    } catch (e) {
      setProgressError(e.message);
      setIsLoading(false);
      return;
    }

    const unsubscribe = subscribeProgress(
      (data) => setProgress(data),
      async () => {
        try {
          const data = await fetchResults();
          setResults(data.results);
          setStep(5);
        } catch (e) {
          setProgressError(e.message);
        } finally {
          setIsLoading(false);
        }
      },
      (err) => {
        setProgressError(err);
        setIsLoading(false);
      }
    );
  }

  function handleReset() {
    setStep(1);
    setTier(null);
    setSfData(null);
    setMatchData(null);
    setMappings({});
    setProgress({ processed: 0, total: 0, done: false });
    setProgressError(null);
    setResults(null);
    setIsLoading(false);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold text-gray-900">STIM Client Matcher</h1>
              <p className="text-xs text-gray-400">Salesforce record matching tool</p>
            </div>
          </div>
          {step > 1 && (
            <button
              onClick={handleReset}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1.5 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Start over
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <Stepper current={step} />

        {/* Step 1 — Tier selection */}
        {step === 1 && (
          <Card
            title="Choose matching tier"
            subtitle="Select the matching method based on what data you have available."
          >
            <TierSelector selected={tier} onSelect={setTier} />
            <div className="mt-8 flex justify-end">
              <button
                disabled={!tier}
                onClick={() => setStep(2)}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg transition-colors"
              >
                Continue →
              </button>
            </div>
          </Card>
        )}

        {/* Step 2 — Salesforce upload */}
        {step === 2 && (
          <Card
            title="Upload Salesforce export"
            subtitle="Required columns: Organisation Number, Account Name, Primary City, Status"
          >
            <FileUpload
              label="Salesforce export"
              onFile={handleSfUpload}
              uploaded={sfData}
              preview={sfData?.preview}
            />
            <div className="mt-8 flex justify-between">
              <button onClick={() => setStep(1)} className="px-5 py-2.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                ← Back
              </button>
              <button
                disabled={!sfData}
                onClick={() => setStep(3)}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg transition-colors"
              >
                Continue →
              </button>
            </div>
          </Card>
        )}

        {/* Step 3 — Match file + column mapping */}
        {step === 3 && (
          <div className="space-y-5">
            <Card
              title="Upload matching file"
              subtitle="Upload the file containing the records you want to match against Salesforce."
            >
              <FileUpload
                label="Matching file"
                onFile={handleMatchUpload}
                uploaded={matchData}
                preview={matchData?.preview}
              />
            </Card>

            {matchData && (
              <Card
                title="Map columns"
                subtitle="Tell us which columns in your file correspond to the required fields."
              >
                <ColumnMapper
                  tier={tier}
                  columns={matchData.columns}
                  mappings={mappings}
                  onChange={setMappings}
                />
              </Card>
            )}

            <div className="flex justify-between">
              <button onClick={() => setStep(2)} className="px-5 py-2.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                ← Back
              </button>
              <button
                disabled={!matchData || !isMappingComplete()}
                onClick={handleRunMatch}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg transition-colors"
              >
                Run matching →
              </button>
            </div>
          </div>
        )}

        {/* Step 4 — Progress */}
        {step === 4 && (
          <Card
            title="Running matching"
            subtitle={`Processing ${matchData?.rowCount?.toLocaleString() ?? "…"} rows against ${sfData?.rowCount?.toLocaleString() ?? "…"} Salesforce records`}
          >
            <div className="py-4">
              <ProgressBar
                processed={progress.processed}
                total={progress.total || matchData?.rowCount || 0}
                error={progressError}
              />
            </div>
            {progressError && (
              <div className="mt-4 flex justify-center">
                <button
                  onClick={() => setStep(3)}
                  className="px-5 py-2.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  ← Back
                </button>
              </div>
            )}
          </Card>
        )}

        {/* Step 5 — Results */}
        {step === 5 && results && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Match Results</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  Tier {tier} — {results.length.toLocaleString()} input rows processed
                </p>
              </div>
              <ExportButton />
            </div>
            <ResultsTable results={results} />
          </div>
        )}
      </main>
    </div>
  );
}
