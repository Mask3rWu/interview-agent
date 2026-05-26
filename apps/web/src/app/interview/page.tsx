"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import { streamAnswer } from "@/lib/sse";

interface Option {
  id: string; name: string; chunk_count?: number; embedding_status?: string;
}

interface ChatMessage {
  role: "interviewer" | "user";
  content: string;
}

type Phase = "setup" | "active" | "ended";

export default function InterviewPage() {
  // Setup state
  const [resumes, setResumes] = useState<Option[]>([]);
  const [jobs, setJobs] = useState<Option[]>([]);
  const [materials, setMaterials] = useState<Option[]>([]);
  const [selResume, setSelResume] = useState("");
  const [selJob, setSelJob] = useState("");
  const [selMaterials, setSelMaterials] = useState<string[]>([]);
  const [materialMode, setMaterialMode] = useState<"none" | "partial" | "all">("partial");
  const [maxRounds, setMaxRounds] = useState(6);

  // Interview state
  const [phase, setPhase] = useState<Phase>("setup");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [answer, setAnswer] = useState("");
  const [streaming, setStreaming] = useState("");
  const [loading, setLoading] = useState(false);
  const [round, setRound] = useState(0);
  const [assessment, setAssessment] = useState<{
    total_score: number; tech_score: number; communication_score: number;
    highlights: string[]; weaknesses: string[]; suggested_review: string[];
  } | null>(null);

  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.listResumes().then(setResumes);
    api.listJobs().then(setJobs);
    api.listMaterials().then(setMaterials);
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const toggleMaterial = (id: string) => {
    setSelMaterials((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const startInterview = async () => {
    setLoading(true);
    try {
      const data = await api.createInterview({
        resume_profile_id: selResume || null,
        job_profile_id: selJob || null,
        material_ids: selMaterials,
        use_all_materials: materialMode === "all",
        max_rounds: maxRounds,
      });
      setSessionId(data.session_id);
      setMessages([{ role: "interviewer", content: data.first_question }]);
      setRound(1);
      setPhase("active");
    } catch (e) {
      alert("创建面试失败: " + (e as Error).message);
    }
    setLoading(false);
  };

  const submitAnswer = useCallback(async () => {
    if (!answer.trim() || loading) return;
    const userMsg = answer;
    setAnswer("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setStreaming("");
    setLoading(true);

    // Try SSE streaming first, fall back to non-streaming
    try {
      await streamAnswer(sessionId, userMsg, {
        onToken: (token) => setStreaming((prev) => prev + token),
        onMessageEnd: (fullText) => {
          setStreaming("");
          setMessages((prev) => [...prev, { role: "interviewer", content: fullText }]);
          setRound((r) => r + 1);
        },
        onAssessment: (data) => {
          setStreaming("");
          setAssessment(data as typeof assessment);
          setPhase("ended");
        },
        onError: async () => {
          // Fallback to non-streaming
          try {
            const res = await api.submitAnswer(sessionId, userMsg);
            if (res.event === "assessment") {
              setAssessment(res.data as typeof assessment);
              setPhase("ended");
            } else if (res.event === "message_end") {
              const text = res.data as string;
              setMessages((prev) => [...prev, { role: "interviewer", content: text }]);
              setRound((r) => r + 1);
            }
          } catch (e) {
            alert("提交失败: " + (e as Error).message);
          }
        },
      });
    } catch {
      // Direct fallback
      try {
        const res = await api.submitAnswer(sessionId, userMsg);
        if (res.event === "assessment") {
          setAssessment(res.data as typeof assessment);
          setPhase("ended");
        } else if (res.event === "message_end") {
          setMessages((prev) => [...prev, { role: "interviewer", content: res.data as string }]);
          setRound((r) => r + 1);
        }
      } catch (e) {
        alert("提交失败: " + (e as Error).message);
      }
    }
    setLoading(false);
  }, [answer, loading, sessionId]);

  const endInterview = async () => {
    setLoading(true);
    try {
      const res = await api.finishInterview(sessionId);
      if (res.event === "assessment") {
        setAssessment(res.data as typeof assessment);
        setPhase("ended");
      }
    } catch (e) {
      alert("结束失败: " + (e as Error).message);
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitAnswer();
    }
  };

  // Setup phase
  if (phase === "setup") {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-6">模拟面试</h1>
        <div className="max-w-lg space-y-5">
          {/* Resume selection */}
          <div>
            <label className="text-sm font-medium text-zinc-600 mb-1 block">选择简历画像</label>
            {resumes.length === 0 && <p className="text-xs text-zinc-400">暂无可选简历</p>}
            <div className="flex flex-wrap gap-2">
              {resumes.map((r) => (
                <button
                  key={r.id}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                    selResume === r.id
                      ? "bg-zinc-900 text-white border-zinc-900"
                      : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                  }`}
                  onClick={() => setSelResume(selResume === r.id ? "" : r.id)}
                >
                  {r.name}
                </button>
              ))}
            </div>
          </div>

          {/* Job selection */}
          <div>
            <label className="text-sm font-medium text-zinc-600 mb-1 block">选择岗位画像</label>
            {jobs.length === 0 && <p className="text-xs text-zinc-400">暂无可选岗位</p>}
            <div className="flex flex-wrap gap-2">
              {jobs.map((j) => (
                <button
                  key={j.id}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                    selJob === j.id
                      ? "bg-zinc-900 text-white border-zinc-900"
                      : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                  }`}
                  onClick={() => setSelJob(selJob === j.id ? "" : j.id)}
                >
                  {j.name}
                </button>
              ))}
            </div>
          </div>

          {/* Materials selection */}
          <div>
            <label className="text-sm font-medium text-zinc-600 mb-2 block">资料策略</label>
            <div className="flex gap-2 mb-3">
              {[
                { key: "none", label: "不使用资料" },
                { key: "partial", label: "部分资料" },
                { key: "all", label: "全部资料" },
              ].map((mode) => (
                <button
                  key={mode.key}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border ${
                    materialMode === mode.key
                      ? "bg-zinc-900 text-white border-zinc-900"
                      : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                  }`}
                  onClick={() => setMaterialMode(mode.key as typeof materialMode)}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            {materials.length === 0 && <p className="text-xs text-zinc-400">暂无可选资料</p>}
            <div className={`flex flex-wrap gap-2 ${materialMode !== "partial" ? "opacity-50 pointer-events-none" : ""}`}>
              {materials.map((m) => (
                <button
                  key={m.id}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                    selMaterials.includes(m.id)
                      ? "bg-zinc-900 text-white border-zinc-900"
                      : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                  }`}
                  onClick={() => toggleMaterial(m.id)}
                >
                  {m.name}
                  {m.chunk_count != null && <span className="ml-1 text-[10px] opacity-70">{m.chunk_count}</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Max rounds */}
          <div>
            <label className="text-sm font-medium text-zinc-600 mb-1 block">
              最大轮次: <span className="font-mono text-zinc-900">{maxRounds}</span>
            </label>
            <input
              type="range"
              min={2}
              max={15}
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <button
            className="w-full rounded-md bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            disabled={loading}
            onClick={startInterview}
          >
            {loading ? "创建中..." : "开始面试"}
          </button>
        </div>
      </div>
    );
  }

  // Active interview
  if (phase === "active") {
    return (
      <div className="flex flex-col h-[calc(100vh-12rem)]">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-semibold">
            模拟面试 <span className="text-sm font-normal text-zinc-400">轮次 {round}/{maxRounds}</span>
          </h1>
          <button
            className="text-xs text-red-500 hover:text-red-600 font-medium"
            onClick={endInterview}
            disabled={loading}
          >
            结束面试
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-zinc-900 text-white"
                    : "bg-white border border-zinc-200 text-zinc-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {streaming && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg px-4 py-2.5 text-sm bg-white border border-zinc-200 text-zinc-800">
                {streaming}
                <span className="inline-block w-1.5 h-4 bg-zinc-400 ml-0.5 animate-pulse align-middle" />
              </div>
            </div>
          )}
          <div ref={chatEnd} />
        </div>

        {/* Input */}
        <div className="flex gap-2 items-end">
          <textarea
            className="flex-1 border border-zinc-300 rounded-lg px-3 py-2.5 text-sm resize-none"
            rows={2}
            placeholder="输入你的回答... (Enter 发送，Shift+Enter 换行)"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            onClick={submitAnswer}
            disabled={loading || !answer.trim()}
          >
            {loading ? "..." : "发送"}
          </button>
        </div>
      </div>
    );
  }

  // Assessment
  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">面试评估报告</h1>

      <div className="rounded-lg border border-zinc-200 bg-white p-6 mb-6">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-zinc-900">{assessment?.total_score ?? "-"}</div>
            <div className="text-xs text-zinc-400 mt-1">总评分</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-zinc-900">{assessment?.tech_score ?? "-"}</div>
            <div className="text-xs text-zinc-400 mt-1">技术能力</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-zinc-900">{assessment?.communication_score ?? "-"}</div>
            <div className="text-xs text-zinc-400 mt-1">沟通表达</div>
          </div>
        </div>

        {assessment && (
          <>
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-emerald-600 mb-2">表现亮点</h3>
              <ul className="space-y-1">
                {assessment.highlights.map((h, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex gap-2">
                    <span className="text-emerald-500">+</span> {h}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-red-500 mb-2">薄弱项</h3>
              <ul className="space-y-1">
                {assessment.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex gap-2">
                    <span className="text-red-400">-</span> {w}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-zinc-700 mb-2">建议复习</h3>
              <div className="flex flex-wrap gap-2">
                {assessment.suggested_review.map((r, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-md bg-zinc-100 text-xs font-medium text-zinc-600">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Chat history */}
      <h2 className="text-sm font-semibold text-zinc-400 mb-3">对话记录</h2>
      <div className="space-y-3">
        {messages.map((m, i) => (
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

      <button
        className="mt-6 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
        onClick={() => {
          setPhase("setup");
          setSessionId("");
          setMessages([]);
          setAssessment(null);
          setRound(0);
        }}
      >
        开始新面试
      </button>
    </div>
  );
}
