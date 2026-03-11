import React from "react";

export default function ProgressBar({ processed, total, error }) {
  const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
  const done = processed >= total && total > 0;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center text-sm">
        <span className="font-medium text-gray-700">
          {error ? (
            <span className="text-red-600">Error: {error}</span>
          ) : done ? (
            <span className="text-green-600 font-semibold">Matching complete</span>
          ) : (
            <span>Processing records…</span>
          )}
        </span>
        <span className="text-gray-500 tabular-nums">
          {processed.toLocaleString()} / {total.toLocaleString()} rows
        </span>
      </div>

      <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-200 ${
            error
              ? "bg-red-500"
              : done
              ? "bg-green-500"
              : "bg-blue-500"
          }`}
          style={{ width: `${pct}%` }}
        />
        {!done && !error && pct > 0 && pct < 100 && (
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background:
                "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)",
              animation: "shimmer 1.5s infinite",
              backgroundSize: "200% 100%",
            }}
          />
        )}
      </div>

      <div className="flex justify-between text-xs text-gray-400">
        <span>{pct}% complete</span>
        {!done && !error && processed > 0 && (
          <span>{(total - processed).toLocaleString()} remaining</span>
        )}
      </div>

      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}
