"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Memory {
  id: string; topic: string; category: string; mastery_score: number;
  exposure_count: number; weakness_count: number;
  last_tested_at: string | null; next_review_at: string | null;
  source_interview_ids?: string[];
}

interface InterviewSummary {
  id: string;
  status: string;
  current_round: number;
  max_rounds: number;
  total_score: number | null;
  created_at: string;
  assessment_status: "pending" | "success" | "failed";
  assessment_error: string;
  memory_update_count: number;
}

const SCORE_COLOR = (s: number) => {
  if (s >= 0.7) return "text-emerald-600";
  if (s >= 0.4) return "text-amber-600";
  return "text-red-500";
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [sortBy, setSortBy] = useState("mastery_score");
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuildResult, setRebuildResult] = useState<string>("");
  const [assessingId, setAssessingId] = useState<string>("");

  const load = async (nextSortBy = sortBy) => {
    const [memoryData, interviewData] = await Promise.all([
      api.listMemories(nextSortBy),
      api.listInterviews(),
    ]);
    setMemories(memoryData as Memory[]);
    setInterviews(interviewData as InterviewSummary[]);
  };

  useEffect(() => {
    Promise.all([api.listMemories(sortBy), api.listInterviews()]).then(([memoryData, interviewData]) => {
      setMemories(memoryData as Memory[]);
      setInterviews(interviewData as InterviewSummary[]);
    });
  }, [sortBy]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const assessmentLabel = (status: InterviewSummary["assessment_status"]) => {
    if (status === "success") return "已评估";
    if (status === "failed") return "评估失败";
    return "未评估";
  };

  const assessmentClass = (status: InterviewSummary["assessment_status"]) => {
    if (status === "success") return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (status === "failed") return "bg-red-50 text-red-600 border-red-200";
    return "bg-amber-50 text-amber-700 border-amber-200";
  };

  const rebuild = async () => {
    setRebuilding(true);
    setRebuildResult("");
    try {
      const result = await api.rebuildMemories();
      if (result.interview_count === 0) {
        setRebuildResult("没有可用于重建的成功评估面试；请先重新评估历史面试或完成一次新面试。");
      } else {
        setRebuildResult(
          `已重评 ${result.interview_count} 场面试，成功 ${result.success_count} 场，失败 ${result.failure_count} 场，生成 ${result.memory_count} 条记忆`
        );
      }
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : "重建失败";
      setRebuildResult(message);
    } finally {
      setRebuilding(false);
    }
  };

  const assessInterview = async (id: string) => {
    setAssessingId(id);
    setRebuildResult("");
    try {
      await api.assessInterview(id);
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : "评估失败";
      setRebuildResult(message);
      await load();
    } finally {
      setAssessingId("");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-6">
        <h1 className="text-xl font-semibold">知识掌握画像</h1>
        <button
          className="px-3 py-1.5 rounded-md text-xs font-medium bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
          disabled={rebuilding}
          onClick={rebuild}
        >
          {rebuilding ? "重建中..." : "从历史重建"}
        </button>
      </div>
      {rebuildResult && (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          {rebuildResult}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        {[
          { key: "mastery_score", label: "掌握度" },
          { key: "exposure_count", label: "考察次数" },
          { key: "weakness_count", label: "薄弱次数" },
          { key: "last_tested_at", label: "最近考察" },
        ].map((opt) => (
          <button
            key={opt.key}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              sortBy === opt.key
                ? "bg-zinc-900 text-white"
                : "bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
            }`}
            onClick={() => setSortBy(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white overflow-hidden mb-8">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-100 text-left">
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">知识点</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">分类</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">掌握度</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">考察/薄弱</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">来源面试</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">下次复习</th>
            </tr>
          </thead>
          <tbody>
            {memories.map((m) => (
              <tr key={m.id} className="border-b border-zinc-50 last:border-0">
                <td className="px-4 py-2.5 font-medium">{m.topic}</td>
                <td className="px-4 py-2.5 text-zinc-500">{m.category || "-"}</td>
                <td className="px-4 py-2.5">
                  <span className={`font-mono font-semibold ${SCORE_COLOR(m.mastery_score)}`}>
                    {(m.mastery_score * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">
                  {m.exposure_count} / {m.weakness_count}
                </td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">
                  {m.source_interview_ids?.length ?? 0}
                </td>
                <td className="px-4 py-2.5 text-zinc-400 text-xs">
                  {m.next_review_at ? m.next_review_at.slice(0, 10) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {memories.length === 0 && (
          <p className="text-sm text-zinc-400 py-12 text-center">
            暂无记忆数据 — 完成一次面试评估后自动生成
          </p>
        )}
      </div>

      <div className="flex items-center justify-between gap-4 mb-3">
        <h2 className="text-base font-semibold">面试历史评估</h2>
        <span className="text-xs text-zinc-400">{interviews.length} 场</span>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-100 text-left">
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">时间</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">轮次</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">评估状态</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">评分</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">记忆更新</th>
              <th className="px-4 py-2.5 font-medium text-zinc-500 text-xs">操作</th>
            </tr>
          </thead>
          <tbody>
            {interviews.map((iv) => (
              <tr key={iv.id} className="border-b border-zinc-50 last:border-0">
                <td className="px-4 py-2.5 text-zinc-600">{formatDate(iv.created_at)}</td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">
                  {iv.current_round}/{iv.max_rounds}
                </td>
                <td className="px-4 py-2.5">
                  <span className={`inline-flex rounded-md border px-2 py-0.5 text-xs ${assessmentClass(iv.assessment_status)}`}>
                    {assessmentLabel(iv.assessment_status)}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-zinc-600">
                  {iv.total_score ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">
                  {iv.memory_update_count}
                </td>
                <td className="px-4 py-2.5">
                  {iv.assessment_status !== "success" ? (
                    <button
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-900 text-white hover:bg-zinc-700 disabled:opacity-50"
                      disabled={assessingId === iv.id}
                      onClick={() => assessInterview(iv.id)}
                    >
                      {assessingId === iv.id ? "评估中..." : "评估"}
                    </button>
                  ) : (
                    <span className="text-xs text-zinc-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {interviews.length === 0 && (
          <p className="text-sm text-zinc-400 py-10 text-center">
            暂无面试历史
          </p>
        )}
      </div>
    </div>
  );
}
