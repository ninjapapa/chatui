import { useEffect, useState } from "react";
import { getJson } from "./api";

type BacklogItem = {
  number: number;
  title: string;
  url: string;
};

type BacklogResponse = {
  repo: string;
  issuesUrl: string;
  items: BacklogItem[];
};

type PmStatus = {
  last: {
    id: string;
    started_at: string;
    finished_at: string | null;
    status: string;
    new_feedback_count: number;
    notes: string | null;
  } | null;
  logPath: string;
};


export default function Backlog() {
  const [data, setData] = useState<BacklogResponse | null>(null);
  const [pm, setPm] = useState<PmStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getJson<BacklogResponse>("/api/backlog")
      .then(setData)
      .catch((e) => setErr(e?.message ?? String(e)));

    getJson<PmStatus>("/api/pm/status")
      .then(setPm)
      .catch(() => {});
  }, []);

  if (err) {
    return (
      <div className="p-4 text-sm">
        <div className="text-red-600">Failed to load backlog: {err}</div>
        <div className="mt-2 text-gray-700">
          You can still view issues directly on GitHub.
        </div>
      </div>
    );
  }

  if (!data) return <div className="p-4 text-sm text-gray-600">Loading backlog…</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-3">Backlog</h2>
      <div className="text-sm mb-3">
        Repo: <span className="font-mono">{data.repo}</span> ·{" "}
        <a className="text-blue-600 underline" href={data.issuesUrl} target="_blank" rel="noreferrer">
          View on GitHub
        </a>
      </div>

      <div className="text-xs text-gray-600 mb-3">
        <div className="font-medium">PM loop</div>
        {pm?.last ? (
          <div>
            Last run: {new Date(pm.last.started_at).toLocaleString()} · status: {pm.last.status} · new feedback: {pm.last.new_feedback_count}
          </div>
        ) : (
          <div>No PM runs yet.</div>
        )}
        <div>Log: <span className="font-mono">{pm?.logPath ?? "backend/data/pm_loop.log"}</span></div>
      </div>

      {data.items.length === 0 ? (
        <div className="text-sm text-gray-600">No open issues.</div>
      ) : (
        <div className="space-y-2">
          {data.items.map((it) => (
            <div key={it.number} className="border rounded p-3">
              <div className="text-sm font-medium">#{it.number} {it.title}</div>
              <a className="text-xs text-blue-600 underline" href={it.url} target="_blank" rel="noreferrer">
                {it.url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
