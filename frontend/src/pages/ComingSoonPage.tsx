export default function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="game-panel p-12 text-center">
      <div className="game-kicker">PAGE NOT FOUND</div>
      <div className="mt-3 text-lg font-semibold">{title}</div>
      <div className="mt-2 text-sm text-[#9bb6c5]">请返回任务大厅继续训练。</div>
    </div>
  );
}
