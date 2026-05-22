"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Job {
  id: string; name: string; company: string; raw_text: string; created_at: string;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<Job | null>(null);

  const load = async () => {
    const data = await api.listJobs();
    setJobs(data as Job[]);
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name || !rawText) return;
    setLoading(true);
    await api.createJob({ name, company, raw_text: rawText });
    setName(""); setCompany(""); setRawText(""); setLoading(false);
    load();
  };

  const toggle = async (id: string) => {
    if (expanded === id) { setExpanded(null); setDetail(null); return; }
    const d = await api.getJob(id);
    setDetail(d as Job);
    setExpanded(id);
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">岗位画像</h1>

      <div className="rounded-lg border border-zinc-200 bg-white p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <input
            className="border border-zinc-300 rounded-md px-3 py-2 text-sm"
            placeholder="岗位名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="border border-zinc-300 rounded-md px-3 py-2 text-sm"
            placeholder="公司名称（可选）"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </div>
        <textarea
          className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
          rows={5}
          placeholder="粘贴 JD 文本..."
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <button
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          disabled={loading || !name || !rawText}
          onClick={create}
        >
          {loading ? "创建中..." : "创建岗位画像"}
        </button>
      </div>

      <div className="space-y-2">
        {jobs.map((j) => (
          <div key={j.id} className="rounded-lg border border-zinc-200 bg-white">
            <button
              className="w-full text-left px-4 py-3 flex justify-between items-center"
              onClick={() => toggle(j.id)}
            >
              <div>
                <span className="font-medium text-sm">{j.name}</span>
                {j.company && <span className="text-xs text-zinc-400 ml-2">@{j.company}</span>}
              </div>
              <span className="text-xs text-zinc-400">{j.created_at?.slice(0, 10)}</span>
            </button>
            {expanded === j.id && detail && (
              <div className="px-4 pb-4 border-t border-zinc-100 pt-3">
                <pre className="text-xs text-zinc-600 whitespace-pre-wrap font-mono">{detail.raw_text}</pre>
              </div>
            )}
          </div>
        ))}
        {jobs.length === 0 && (
          <p className="text-sm text-zinc-400 py-8 text-center">暂无岗位画像，在上方创建第一个</p>
        )}
      </div>
    </div>
  );
}
