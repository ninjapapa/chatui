import { useEffect, useState } from "react";
import { getJson } from "./api";

type ChangelogEntry = {
  id: string;
  title: string;
  body_md: string;
  created_at: string;
};

export default function Changelog() {
  const [items, setItems] = useState<ChangelogEntry[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getJson<ChangelogEntry[]>("/api/changelog?limit=30")
      .then(setItems)
      .catch((e) => setErr(e?.message ?? String(e)));
  }, []);

  if (err) return <div className="p-4 text-sm text-red-600">Failed to load changelog: {err}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-3">Changelog</h2>
      {items.length === 0 ? (
        <div className="text-sm text-gray-600">No entries yet.</div>
      ) : (
        <div className="space-y-3">
          {items.map((c) => (
            <div key={c.id} className="border rounded p-3">
              <div className="flex justify-between gap-3">
                <div className="font-medium">{c.title}</div>
                <div className="text-xs text-gray-500">{new Date(c.created_at).toLocaleString()}</div>
              </div>
              <pre className="text-sm whitespace-pre-wrap mt-2">{c.body_md}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
