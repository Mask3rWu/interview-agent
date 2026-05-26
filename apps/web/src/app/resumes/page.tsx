"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Resume {
  id: string; name: string; raw_text: string; created_at: string;
  markdown_path?: string;
  summary_json?: { summary?: string };
  skills_json?: Record<string, string[]>;
  project_highlights?: string[];
  potential_questions_json?: string[];
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [name, setName] = useState("");
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<Resume | null>(null);

  const load = async () => {
    const data = await api.listResumes();
    setResumes(data as Resume[]);
  };

  useEffect(() => {
    let mounted = true;
    api.listResumes().then((data) => {
      if (mounted) setResumes(data as Resume[]);
    });
    return () => { mounted = false; };
  }, []);

  const create = async () => {
    if (!name || !rawText) return;
    setLoading(true);
    await api.createResume({ name, raw_text: rawText });
    setName(""); setRawText(""); setLoading(false);
    load();
  };

  const toggle = async (id: string) => {
    if (expanded === id) {
      setExpanded(null); setDetail(null); return;
    }
    const d = await api.getResume(id);
    setDetail(d as Resume);
    setExpanded(id);
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">简历画像</h1>

      <div className="rounded-lg border border-zinc-200 bg-white p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <input
            className="border border-zinc-300 rounded-md px-3 py-2 text-sm"
            placeholder="画像名称，如 张三-后端"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <textarea
          className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
          rows={5}
          placeholder="粘贴简历文本..."
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <button
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          disabled={loading || !name || !rawText}
          onClick={create}
        >
          {loading ? "创建中..." : "创建简历画像"}
        </button>
      </div>

      <div className="space-y-2">
        {resumes.map((r) => (
          <div key={r.id} className="rounded-lg border border-zinc-200 bg-white">
            <button
              className="w-full text-left px-4 py-3 flex justify-between items-center"
              onClick={() => toggle(r.id)}
            >
              <span className="font-medium text-sm">{r.name}</span>
              <span className="text-xs text-zinc-400">{r.created_at?.slice(0, 10)}</span>
            </button>
            {expanded === r.id && detail && (
              <div className="px-4 pb-4 border-t border-zinc-100 pt-3 space-y-4">
                <div>
                  <h3 className="text-xs font-semibold text-zinc-500 mb-1">摘要</h3>
                  <p className="text-sm text-zinc-700">{detail.summary_json?.summary || "暂无摘要"}</p>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-zinc-500 mb-2">技能矩阵</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(detail.skills_json || {}).flatMap(([group, skills]) =>
                      skills.map((skill) => (
                        <span key={`${group}-${skill}`} className="rounded-md bg-zinc-100 px-2 py-1 text-xs text-zinc-600">
                          {group}: {skill}
                        </span>
                      ))
                    )}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-zinc-500 mb-2">潜在追问</h3>
                  <ul className="space-y-1 text-sm text-zinc-600">
                    {(detail.potential_questions_json || []).map((q, i) => <li key={i}>- {q}</li>)}
                  </ul>
                </div>
                <pre className="text-xs text-zinc-500 whitespace-pre-wrap font-mono">{detail.raw_text}</pre>
              </div>
            )}
          </div>
        ))}
        {resumes.length === 0 && (
          <p className="text-sm text-zinc-400 py-8 text-center">暂无简历画像，在上方创建第一个</p>
        )}
      </div>
    </div>
  );
}
