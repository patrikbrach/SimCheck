import React, { useMemo, useState } from "react";

function ScoreBadge({ score }) {
  const s = Number(score);
  let cls = "bg-red-100 text-red-700";
  if (s >= 90) cls = "bg-green-100 text-green-700";
  else if (s >= 70) cls = "bg-amber-100 text-amber-700";
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold tabular-nums ${cls}`}>
      {s}%
    </span>
  );
}

function RowColor(score) {
  const s = Number(score);
  if (s >= 90) return "bg-green-50";
  if (s >= 70) return "bg-amber-50";
  return "bg-red-50";
}

export default function ResultsTable({ results }) {
  const [sortDir, setSortDir] = useState("desc");
  const [filterQuery, setFilterQuery] = useState("");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 50;

  const inputKeys = useMemo(() => {
    if (!results?.length) return [];
    const keys = new Set();
    results.forEach((r) => Object.keys(r.input || {}).forEach((k) => keys.add(k)));
    return Array.from(keys);
  }, [results]);

  const flatRows = useMemo(() => {
    if (!results) return [];
    const rows = [];
    results.forEach((item, idx) => {
      const candidates = item.candidates || [];
      if (candidates.length === 0) {
        rows.push({ inputIdx: idx, input: item.input, rank: null, candidate: null });
      } else {
        candidates.forEach((cand, ri) => {
          rows.push({ inputIdx: idx, input: item.input, rank: ri + 1, candidate: cand });
        });
      }
    });
    return rows;
  }, [results]);

  const filtered = useMemo(() => {
    if (!filterQuery.trim()) return flatRows;
    const q = filterQuery.toLowerCase();
    return flatRows.filter((r) => {
      const inputStr = Object.values(r.input || {}).join(" ").toLowerCase();
      const candStr = r.candidate
        ? [r.candidate.account_name, r.candidate.org_nr, r.candidate.city, r.candidate.status].join(" ").toLowerCase()
        : "";
      return inputStr.includes(q) || candStr.includes(q);
    });
  }, [flatRows, filterQuery]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const sa = a.candidate?.score ?? -1;
      const sb = b.candidate?.score ?? -1;
      return sortDir === "desc" ? sb - sa : sa - sb;
    });
  }, [filtered, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const paginated = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const stats = useMemo(() => {
    const inputRows = results?.length || 0;
    const withMatches = results?.filter((r) => r.candidates?.length > 0).length || 0;
    const highConf = results?.filter((r) => (r.candidates?.[0]?.score ?? 0) >= 90).length || 0;
    return { inputRows, withMatches, highConf };
  }, [results]);

  if (!results?.length) return null;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Input rows", value: stats.inputRows },
          { label: "Matched", value: stats.withMatches },
          { label: "High confidence (≥90%)", value: stats.highConf },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{s.value.toLocaleString()}</div>
            <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Filter results…"
            value={filterQuery}
            onChange={(e) => { setFilterQuery(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
          className="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition-colors"
        >
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d={sortDir === "desc"
                ? "M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
                : "M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"} />
          </svg>
          Score {sortDir === "desc" ? "↓" : "↑"}
        </button>
        <span className="text-sm text-gray-400">{filtered.length.toLocaleString()} rows</span>
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-xs">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-green-100 border border-green-300" /> ≥90% high confidence</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-amber-100 border border-amber-300" /> 70–89% medium</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-red-100 border border-red-300" /> &lt;70% low confidence</span>
      </div>

      {/* Table */}
      <div className="overflow-auto rounded-xl border border-gray-200 shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {inputKeys.map((k) => (
                <th key={k} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  {k}
                </th>
              ))}
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Rank</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Method</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">SF Org Nr</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">SF Account Name</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">SF City</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">SF Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {paginated.map((row, i) => {
              const c = row.candidate;
              const rowBg = c ? RowColor(c.score) : "bg-gray-50";
              return (
                <tr key={i} className={`${rowBg} hover:brightness-95 transition-all`}>
                  {inputKeys.map((k) => (
                    <td key={k} className="px-3 py-2.5 text-gray-700 whitespace-nowrap max-w-xs truncate">
                      {String(row.input?.[k] ?? "")}
                    </td>
                  ))}
                  {c ? (
                    <>
                      <td className="px-3 py-2.5 text-center">
                        <span className={`inline-block w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center ${
                          row.rank === 1 ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-600"
                        }`}>{row.rank}</span>
                      </td>
                      <td className="px-3 py-2.5"><ScoreBadge score={c.score} /></td>
                      <td className="px-3 py-2.5 text-gray-500 text-xs font-mono whitespace-nowrap">{c.method}</td>
                      <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{c.org_nr}</td>
                      <td className="px-3 py-2.5 text-gray-900 font-medium whitespace-nowrap">{c.account_name}</td>
                      <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{c.city}</td>
                      <td className="px-3 py-2.5">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{c.status}</span>
                      </td>
                    </>
                  ) : (
                    <td colSpan={7} className="px-3 py-2.5 text-gray-400 italic text-sm">No match found</td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
