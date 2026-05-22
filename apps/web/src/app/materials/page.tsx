"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Material {
  id: string; name: string; type: string; raw_text: string; enabled: boolean; created_at: string;
}

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [name, setName] = useState("");
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<Material | null>(null);

  const load = async () => {
    const data = await api.listMaterials();
    setMaterials(data as Material[]);
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name || !rawText) return;
    setLoading(true);
    await api.createMaterial({ name, raw_text: rawText });
    setName(""); setRawText(""); setLoading(false);
    load();
  };

  const toggle = async (id: string) => {
    if (expanded === id) { setExpanded(null); setDetail(null); return; }
    const d = await api.getMaterial(id);
    setDetail(d as Material);
    setExpanded(id);
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">面试资料</h1>

      <div className="rounded-lg border border-zinc-200 bg-white p-4 mb-6">
        <input
          className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
          placeholder="资料名称，如 Redis 面试题集"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <textarea
          className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
          rows={6}
          placeholder="粘贴 Markdown 资料内容...&#10;&#10;## 章节标题&#10;内容..."
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <button
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          disabled={loading || !name || !rawText}
          onClick={create}
        >
          {loading ? "创建中..." : "创建资料"}
        </button>
      </div>

      <div className="space-y-2">
        {materials.map((m) => (
          <div key={m.id} className="rounded-lg border border-zinc-200 bg-white">
            <button
              className="w-full text-left px-4 py-3 flex justify-between items-center"
              onClick={() => toggle(m.id)}
            >
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{m.name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-500">{m.type}</span>
              </div>
              <span className="text-xs text-zinc-400">{m.created_at?.slice(0, 10)}</span>
            </button>
            {expanded === m.id && detail && (
              <div className="px-4 pb-4 border-t border-zinc-100 pt-3">
                <pre className="text-xs text-zinc-600 whitespace-pre-wrap font-mono">{detail.raw_text}</pre>
              </div>
            )}
          </div>
        ))}
        {materials.length === 0 && (
          <p className="text-sm text-zinc-400 py-8 text-center">暂无面试资料，在上方创建第一个</p>
        )}
      </div>
    </div>
  );
}
