"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Material {
  id: string; name: string; type: string; raw_text: string; enabled: boolean; created_at: string;
  chunk_count: number; embedding_status: string; markdown_path?: string;
  source_file_path?: string; processing_error?: string;
}

export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [name, setName] = useState("");
  const [rawText, setRawText] = useState("");
  const [pdfName, setPdfName] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<Material | null>(null);
  const [reprocessing, setReprocessing] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await api.listMaterials();
      setMaterials(data as Material[]);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    let mounted = true;
    api.listMaterials()
      .then((data) => {
        if (mounted) {
          setMaterials(data as Material[]);
          setError("");
        }
      })
      .catch((e) => {
        if (mounted) setError((e as Error).message);
      });
    return () => { mounted = false; };
  }, []);

  const create = async () => {
    if (!name || !rawText) return;
    setLoading(true);
    try {
      await api.createMaterial({ name, raw_text: rawText });
      setName(""); setRawText("");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const uploadPdf = async () => {
    if (!pdfFile) return;
    const materialName = pdfName || pdfFile.name.replace(/\.pdf$/i, "");
    setUploading(true);
    try {
      await api.uploadMaterialPdf({ name: materialName, file: pdfFile });
      setPdfName(""); setPdfFile(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  const toggle = async (id: string) => {
    if (expanded === id) { setExpanded(null); setDetail(null); return; }
    const d = await api.getMaterial(id);
    setDetail(d as Material);
    setExpanded(id);
  };

  const reprocess = async (id: string) => {
    setReprocessing(id);
    try {
      const d = await api.reprocessMaterial(id);
      setDetail(d as Material);
      await load();
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setReprocessing(null);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">面试资料</h1>
      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          API 请求失败：{error}
        </div>
      )}

      <div className="rounded-lg border border-zinc-200 bg-white p-4 mb-6">
        <div className="mb-4 border-b border-zinc-100 pb-4">
          <input
            className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
            placeholder="PDF 资料名称，可留空使用文件名"
            value={pdfName}
            onChange={(e) => setPdfName(e.target.value)}
          />
          <input
            className="w-full border border-zinc-300 rounded-md px-3 py-2 text-sm mb-3"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
          />
          <button
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            disabled={uploading || !pdfFile}
            onClick={uploadPdf}
          >
            {uploading ? "上传中..." : "上传 PDF"}
          </button>
        </div>
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
                <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">
                  {m.chunk_count} chunks
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  m.embedding_status === "ready" ? "bg-emerald-50 text-emerald-700" :
                  m.embedding_status === "failed" ? "bg-red-50 text-red-700" :
                  "bg-amber-50 text-amber-700"
                }`}>{m.embedding_status}</span>
              </div>
              <span className="text-xs text-zinc-400">{m.created_at?.slice(0, 10)}</span>
            </button>
            {expanded === m.id && detail && (
              <div className="px-4 pb-4 border-t border-zinc-100 pt-3">
                <div className="mb-3 flex flex-wrap gap-2 text-xs text-zinc-500">
                  <span>Markdown: {detail.markdown_path || "-"}</span>
                  <span>Chunks: {detail.chunk_count}</span>
                  {detail.source_file_path && <span>Source: {detail.source_file_path}</span>}
                </div>
                {detail.type === "pdf" && detail.source_file_path && (
                  <button
                    className="mb-3 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                    disabled={reprocessing === detail.id}
                    onClick={() => reprocess(detail.id)}
                  >
                    {reprocessing === detail.id ? "重新处理中..." : "重新处理 PDF"}
                  </button>
                )}
                {detail.processing_error && (
                  <div className="mb-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
                    {detail.processing_error}
                  </div>
                )}
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
