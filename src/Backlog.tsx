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

export default function Backlog() {
  const [data, setData] = useState<BacklogResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getJson<BacklogResponse>("/api/backlog")
      .then(setData)
      .catch((e) => setErr(e?.message ?? String(e)));
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
