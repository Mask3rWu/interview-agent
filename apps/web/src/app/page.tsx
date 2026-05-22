import Link from "next/link";

const CARDS = [
  { href: "/resumes", title: "简历画像", desc: "上传简历，生成结构化画像" },
  { href: "/jobs", title: "岗位画像", desc: "分析 JD，提取核心要求" },
  { href: "/materials", title: "面试资料", desc: "管理参考资料，为 RAG 做准备" },
  { href: "/interview", title: "模拟面试", desc: "选择画像和资料，开始面试" },
  { href: "/memory", title: "长期记忆", desc: "查看知识点掌握情况" },
];

export default function HomePage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-2">智能模拟面试系统</h1>
      <p className="text-zinc-500 mb-8">单用户多画像面试对练，基于 LangGraph + RAG + 长期记忆</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {CARDS.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="rounded-xl border border-zinc-200 bg-white p-6 hover:border-zinc-300 hover:shadow-sm transition-shadow"
          >
            <h2 className="font-semibold text-lg mb-1">{c.title}</h2>
            <p className="text-sm text-zinc-500">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
