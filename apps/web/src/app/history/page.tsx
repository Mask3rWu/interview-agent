"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface InterviewSummary {
  id: string;
  status: string;
  current_round: number;
  max_rounds: number;
  total_score: number | null;
  created_at: string;
}

interface AssessmentResult {
  total_score: number;
  tech_score: number;
  communication_score: number;
  highlights: string[];
  weaknesses: string[];
  suggested_review: string[];
}

interface ChatMessage {
  role: "interviewer" | "user";
  content: string;
}

interface InterviewDetail {
  id: string;
  status: string;
  messages: ChatMessage[];
  current_round: number;
  max_rounds: number;
  assessment: AssessmentResult | null;
  created_at: string;
}

export default function HistoryPage() {
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<InterviewDetail | null>(null);

  useEffect(() => {
    api.listInterviews().then(setInterviews).finally(() => setLoading(false));
  }, []);

  const openDetail = async (id: string) => {
    try {
      const detail = await api.getInterview(id);
      setSelected(detail as InterviewDetail);
    } catch {
      alert("加载面试详情失败");
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString("zh-CN", {
      month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit",
    });
  };

  const statusLabel = (s: string) => s === "active" ? "进行中" : "已结束";

  // Detail view
  if (selected) {
    const a = selected.assessment;
    return (
      <div>
        <button
          className="text-sm text-zinc-500 hover:text-zinc-900 mb-4 flex items-center gap-1"
          onClick={() => setSelected(null)}
        >
          ← 返回列表
        </button>

        <h1 className="text-xl font-semibold mb-2">面试详情</h1>
        <p className="text-xs text-zinc-400 mb-6">
          {formatDate(selected.created_at)} · {selected.current_round}/{selected.max_rounds} 轮 · {statusLabel(selected.status)}
        </p>

        {a && (
          <div className="rounded-lg border border-zinc-200 bg-white p-6 mb-6">
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-zinc-900">{a.total_score}</div>
                <div className="text-xs text-zinc-400 mt-1">总评分</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-zinc-900">{a.tech_score}</div>
                <div className="text-xs text-zinc-400 mt-1">技术能力</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-zinc-900">{a.communication_score}</div>
                <div className="text-xs text-zinc-400 mt-1">沟通表达</div>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-emerald-600 mb-2">表现亮点</h3>
              <ul className="space-y-1">
                {a.highlights.map((h, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex gap-2">
                    <span className="text-emerald-500">+</span> {h}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-red-500 mb-2">薄弱项</h3>
              <ul className="space-y-1">
                {a.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex gap-2">
                    <span className="text-red-400">-</span> {w}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-zinc-700 mb-2">建议复习</h3>
              <div className="flex flex-wrap gap-2">
                {a.suggested_review.map((r, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-md bg-zinc-100 text-xs font-medium text-zinc-600">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        <h2 className="text-sm font-semibold text-zinc-400 mb-3">对话记录</h2>
        <div className="space-y-3">
          {selected.messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-zinc-900 text-white"
                    : "bg-white border border-zinc-200 text-zinc-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // List view
  if (loading) {
    return <p className="text-sm text-zinc-400">加载中...</p>;
  }

  if (interviews.length === 0) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-4">面试历史</h1>
        <p className="text-sm text-zinc-400">暂无面试记录，去<a href="/interview" className="text-zinc-900 underline ml-1">开始模拟面试</a></p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">面试历史</h1>
      <div className="space-y-3">
        {interviews.map((iv) => (
          <button
            key={iv.id}
            className="w-full text-left rounded-lg border border-zinc-200 bg-white p-4 hover:border-zinc-300 transition-colors"
            onClick={() => openDetail(iv.id)}
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-zinc-900">
                  {formatDate(iv.created_at)}
                </span>
                <span className={`ml-3 text-xs px-2 py-0.5 rounded-full font-medium ${
                  iv.status === "active"
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-zinc-100 text-zinc-500"
                }`}>
                  {statusLabel(iv.status)}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-zinc-400">
                <span>{iv.current_round}/{iv.max_rounds} 轮</span>
                {iv.total_score != null && (
                  <span className="font-mono font-semibold text-zinc-900 text-sm">
                    {iv.total_score} 分
                  </span>
                )}
                <span className="text-zinc-300">→</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
